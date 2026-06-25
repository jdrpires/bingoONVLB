from bingo_app.models import User


def test_dashboard_requires_login(client):
    response = client.get("/painel")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_user_can_register_and_logout(client, app):
    response = client.post(
        "/auth/cadastro",
        data={
            "name": "Maria",
            "email": "maria@example.com",
            "password": "senha-segura",
            "password_confirmation": "senha-segura",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Seus bingos" in response.data

    with app.app_context():
        user = User.query.filter_by(email="maria@example.com").one()
        assert user.password_hash != "senha-segura"
        assert user.check_password("senha-segura")

    response = client.post("/auth/logout", follow_redirects=True)
    assert b"Entrar" in response.data


def test_login_rejects_invalid_password(client, app):
    client.post(
        "/auth/cadastro",
        data={
            "name": "João",
            "email": "joao@example.com",
            "password": "senha-segura",
            "password_confirmation": "senha-segura",
        },
    )
    client.post("/auth/logout")

    response = client.post(
        "/auth/login",
        data={"email": "joao@example.com", "password": "senha-errada"},
        follow_redirects=True,
    )
    assert "E-mail ou senha inválidos.".encode() in response.data
