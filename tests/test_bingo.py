from bingo_app.models import Bingo, BingoRound, Draw, RoundEvent, bingo_letter


def register(client, name, email):
    return client.post(
        "/auth/cadastro",
        data={
            "name": name,
            "email": email,
            "password": "senha-segura",
            "password_confirmation": "senha-segura",
        },
        follow_redirects=True,
    )


def test_user_can_create_bingo_round_and_draw_without_duplicates(client, app):
    register(client, "Maria", "maria@example.com")

    response = client.post(
        "/bingos/novo",
        data={"name": "Bingo da comunidade"},
        follow_redirects=True,
    )
    assert b"Bingo da comunidade" in response.data

    with app.app_context():
        bingo_id = Bingo.query.one().id

    client.post(f"/bingos/{bingo_id}/rodadas")
    for _ in range(75):
        response = client.post(f"/bingos/{bingo_id}/sortear")
        assert response.status_code == 302

    with app.app_context():
        round_ = BingoRound.query.one()
        numbers = [draw.number for draw in Draw.query.filter_by(round_id=round_.id).all()]
        assert len(numbers) == 75
        assert len(set(numbers)) == 75
        assert set(numbers) == set(range(1, 76))


def test_user_cannot_access_another_users_bingo(client, app):
    register(client, "Maria", "maria@example.com")
    client.post("/bingos/novo", data={"name": "Bingo privado"})
    with app.app_context():
        bingo_id = Bingo.query.one().id
    client.post("/auth/logout")

    register(client, "João", "joao@example.com")
    assert client.get(f"/bingos/{bingo_id}").status_code == 403
    assert client.post(f"/bingos/{bingo_id}/rodadas").status_code == 403


def test_only_one_round_can_be_active(client, app):
    register(client, "Maria", "maria@example.com")
    client.post("/bingos/novo", data={"name": "Bingo teste"})
    with app.app_context():
        bingo_id = Bingo.query.one().id

    client.post(f"/bingos/{bingo_id}/rodadas")
    client.post(f"/bingos/{bingo_id}/rodadas")

    with app.app_context():
        assert BingoRound.query.count() == 1


def test_public_screen_exposes_current_round_without_login(client, app):
    register(client, "Maria", "maria@example.com")
    client.post("/bingos/novo", data={"name": "Bingo público"})
    with app.app_context():
        bingo = Bingo.query.one()
        bingo_id = bingo.id
        public_id = bingo.public_id

    client.post(f"/bingos/{bingo_id}/rodadas")
    client.post(f"/bingos/{bingo_id}/sortear")
    client.post("/auth/logout")

    page = client.get(f"/sala/{public_id}")
    state = client.get(f"/api/salas/{public_id}")

    assert page.status_code == 200
    assert b"Bingo p\xc3\xbablico" in page.data
    assert b'id="public-letter"' in page.data
    assert b'id="public-number"' in page.data
    assert b"public-game.js?v=3" in page.data
    assert b"code-synergy-logo.png" in page.data
    assert b"styles.css?v=code-synergy-2" in page.data
    assert state.status_code == 200
    assert state.json["status"] == "active"
    assert len(state.json["drawn_numbers"]) == 1
    assert state.json["last_call"][0] in "BINGO"


def test_pause_and_bingo_check_block_new_draws(client, app):
    register(client, "Maria", "maria@example.com")
    client.post("/bingos/novo", data={"name": "Bingo seguro"})
    with app.app_context():
        bingo_id = Bingo.query.one().id

    client.post(f"/bingos/{bingo_id}/rodadas")
    client.post(f"/bingos/{bingo_id}/sortear")
    client.post(f"/bingos/{bingo_id}/pausar")
    client.post(f"/bingos/{bingo_id}/sortear")

    with app.app_context():
        assert BingoRound.query.one().status == "paused"
        assert Draw.query.count() == 1

    client.post(f"/bingos/{bingo_id}/retomar")
    client.post(f"/bingos/{bingo_id}/conferir")
    client.post(f"/bingos/{bingo_id}/sortear")

    with app.app_context():
        assert BingoRound.query.one().status == "checking"
        assert Draw.query.count() == 1


def test_undo_last_draw_is_audited_and_position_is_reused(client, app):
    register(client, "Maria", "maria@example.com")
    client.post("/bingos/novo", data={"name": "Bingo auditado"})
    with app.app_context():
        bingo_id = Bingo.query.one().id

    client.post(f"/bingos/{bingo_id}/rodadas")
    client.post(f"/bingos/{bingo_id}/sortear")
    client.post(f"/bingos/{bingo_id}/sortear")
    client.post(f"/bingos/{bingo_id}/desfazer")

    with app.app_context():
        assert Draw.query.count() == 1
        assert RoundEvent.query.filter_by(event_type="draw_undone").count() == 1

    client.post(f"/bingos/{bingo_id}/sortear")
    with app.app_context():
        assert [draw.position for draw in Draw.query.order_by(Draw.position)] == [1, 2]


def test_round_csv_contains_draws_and_audit_events(client, app):
    register(client, "Maria", "maria@example.com")
    client.post("/bingos/novo", data={"name": "Bingo ata"})
    with app.app_context():
        bingo_id = Bingo.query.one().id

    client.post(f"/bingos/{bingo_id}/rodadas")
    client.post(f"/bingos/{bingo_id}/sortear")
    with app.app_context():
        round_id = BingoRound.query.one().id

    response = client.get(f"/bingos/{bingo_id}/rodadas/{round_id}/ata.csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "Eventos de auditoria".encode() in response.data
    assert "number_drawn".encode() in response.data


def test_bingo_letters_follow_standard_ranges():
    assert bingo_letter(1) == "B"
    assert bingo_letter(15) == "B"
    assert bingo_letter(16) == "I"
    assert bingo_letter(30) == "I"
    assert bingo_letter(31) == "N"
    assert bingo_letter(45) == "N"
    assert bingo_letter(46) == "G"
    assert bingo_letter(60) == "G"
    assert bingo_letter(61) == "O"
    assert bingo_letter(75) == "O"
