import secrets
import csv
import io
from datetime import datetime, timezone

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user, login_required

from .extensions import db
from .forms import BingoForm
from .models import Bingo, BingoRound, Draw, RoundEvent, bingo_letter


main_bp = Blueprint("main", __name__)


@main_bp.get("/health")
def health():
    return {"status": "ok"}


@main_bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.get("/painel")
@login_required
def dashboard():
    bingos = Bingo.query.filter_by(owner_id=current_user.id).order_by(Bingo.created_at.desc()).all()
    return render_template("dashboard.html", bingos=bingos)


@main_bp.route("/bingos/novo", methods=["GET", "POST"])
@login_required
def create_bingo():
    form = BingoForm()
    if form.validate_on_submit():
        bingo = Bingo(name=form.name.data.strip(), owner_id=current_user.id)
        db.session.add(bingo)
        db.session.commit()
        flash("Bingo criado. Agora você pode iniciar a primeira rodada.", "success")
        return redirect(url_for("main.bingo_detail", bingo_id=bingo.id))
    return render_template("bingos/create.html", form=form)


def get_owned_bingo_or_404(bingo_id):
    bingo = db.session.get(Bingo, bingo_id)
    if not bingo:
        abort(404)
    if bingo.owner_id != current_user.id:
        abort(403)
    return bingo


@main_bp.get("/bingos/<int:bingo_id>")
@login_required
def bingo_detail(bingo_id):
    bingo = get_owned_bingo_or_404(bingo_id)
    return render_template("bingos/detail.html", bingo=bingo, numbers=range(1, 76))


@main_bp.post("/bingos/<int:bingo_id>/rodadas")
@login_required
def create_round(bingo_id):
    bingo = get_owned_bingo_or_404(bingo_id)
    if bingo.active_round:
        flash("Encerre a rodada atual antes de iniciar outra.", "warning")
        return redirect(url_for("main.bingo_detail", bingo_id=bingo.id))

    next_number = max((round_.number for round_ in bingo.rounds), default=0) + 1
    round_ = BingoRound(number=next_number, bingo=bingo)
    db.session.add(round_)
    db.session.add(
        RoundEvent(
            event_type="round_started",
            description=f"Rodada {next_number} iniciada.",
            round=round_,
        )
    )
    db.session.commit()
    flash(f"Rodada {next_number} iniciada.", "success")
    return redirect(url_for("main.bingo_detail", bingo_id=bingo.id))


@main_bp.post("/bingos/<int:bingo_id>/sortear")
@login_required
def draw_number(bingo_id):
    bingo = get_owned_bingo_or_404(bingo_id)
    round_ = bingo.active_round
    if not round_:
        flash("Inicie uma rodada antes de sortear.", "warning")
        return redirect(url_for("main.bingo_detail", bingo_id=bingo.id))
    if round_.status != "active":
        flash("Retome a rodada antes de sortear um novo número.", "warning")
        return redirect(url_for("main.bingo_detail", bingo_id=bingo.id))

    drawn = set(round_.drawn_numbers)
    remaining = [number for number in range(1, 76) if number not in drawn]
    if not remaining:
        flash("Todos os 75 números já foram sorteados.", "info")
        return redirect(url_for("main.bingo_detail", bingo_id=bingo.id))

    draw = Draw(
        number=secrets.choice(remaining),
        position=len(drawn) + 1,
        round=round_,
    )
    db.session.add(draw)
    db.session.add(
        RoundEvent(
            event_type="number_drawn",
            description=f"{bingo_letter(draw.number)}-{draw.number} sorteado na posição {draw.position}.",
            round=round_,
        )
    )
    db.session.commit()
    return redirect(url_for("main.bingo_detail", bingo_id=bingo.id))


@main_bp.post("/bingos/<int:bingo_id>/encerrar")
@login_required
def finish_round(bingo_id):
    bingo = get_owned_bingo_or_404(bingo_id)
    round_ = bingo.active_round
    if not round_:
        flash("Não existe rodada ativa.", "warning")
    else:
        round_.status = "finished"
        round_.finished_at = datetime.now(timezone.utc)
        db.session.add(
            RoundEvent(
                event_type="round_finished",
                description=f"Rodada {round_.number} encerrada.",
                round=round_,
            )
        )
        db.session.commit()
        flash(f"Rodada {round_.number} encerrada.", "success")
    return redirect(url_for("main.bingo_detail", bingo_id=bingo.id))


@main_bp.post("/bingos/<int:bingo_id>/pausar")
@login_required
def pause_round(bingo_id):
    bingo = get_owned_bingo_or_404(bingo_id)
    round_ = bingo.active_round
    if not round_ or round_.status != "active":
        flash("A rodada não está em andamento.", "warning")
    else:
        round_.status = "paused"
        db.session.add(
            RoundEvent(event_type="round_paused", description="Rodada pausada.", round=round_)
        )
        db.session.commit()
        flash("Rodada pausada.", "success")
    return redirect(url_for("main.bingo_detail", bingo_id=bingo.id))


@main_bp.post("/bingos/<int:bingo_id>/retomar")
@login_required
def resume_round(bingo_id):
    bingo = get_owned_bingo_or_404(bingo_id)
    round_ = bingo.active_round
    if not round_ or round_.status not in {"paused", "checking"}:
        flash("A rodada não está pausada.", "warning")
    else:
        previous_status = round_.status
        round_.status = "active"
        description = (
            "Conferência encerrada e rodada retomada."
            if previous_status == "checking"
            else "Rodada retomada."
        )
        db.session.add(
            RoundEvent(event_type="round_resumed", description=description, round=round_)
        )
        db.session.commit()
        flash(description, "success")
    return redirect(url_for("main.bingo_detail", bingo_id=bingo.id))


@main_bp.post("/bingos/<int:bingo_id>/conferir")
@login_required
def check_bingo(bingo_id):
    bingo = get_owned_bingo_or_404(bingo_id)
    round_ = bingo.active_round
    if not round_:
        flash("Não existe rodada ativa.", "warning")
    else:
        round_.status = "checking"
        db.session.add(
            RoundEvent(
                event_type="bingo_check",
                description="BINGO anunciado. Sorteio interrompido para conferência.",
                round=round_,
            )
        )
        db.session.commit()
        flash("Sorteio interrompido para conferência do BINGO.", "success")
    return redirect(url_for("main.bingo_detail", bingo_id=bingo.id))


@main_bp.post("/bingos/<int:bingo_id>/desfazer")
@login_required
def undo_last_draw(bingo_id):
    bingo = get_owned_bingo_or_404(bingo_id)
    round_ = bingo.active_round
    if not round_ or not round_.draws:
        flash("Não existe sorteio para desfazer.", "warning")
        return redirect(url_for("main.bingo_detail", bingo_id=bingo.id))

    draw = round_.draws[-1]
    description = (
        f"Sorteio {bingo_letter(draw.number)}-{draw.number}, posição {draw.position}, desfeito."
    )
    db.session.delete(draw)
    db.session.add(
        RoundEvent(event_type="draw_undone", description=description, round=round_)
    )
    db.session.commit()
    flash(description, "success")
    return redirect(url_for("main.bingo_detail", bingo_id=bingo.id))


@main_bp.get("/bingos/<int:bingo_id>/rodadas/<int:round_id>/ata.csv")
@login_required
def export_round_csv(bingo_id, round_id):
    bingo = get_owned_bingo_or_404(bingo_id)
    round_ = db.session.get(BingoRound, round_id)
    if not round_ or round_.bingo_id != bingo.id:
        abort(404)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Bingo", bingo.name])
    writer.writerow(["Rodada", round_.number])
    writer.writerow(["Status", round_.status])
    writer.writerow([])
    writer.writerow(["Posição", "Letra", "Número", "Data/hora UTC"])
    for draw in round_.draws:
        writer.writerow(
            [
                draw.position,
                draw.letter,
                draw.number,
                draw.created_at.isoformat(),
            ]
        )
    writer.writerow([])
    writer.writerow(["Eventos de auditoria"])
    writer.writerow(["Tipo", "Descrição", "Data/hora UTC"])
    for event in round_.events:
        writer.writerow([event.event_type, event.description, event.created_at.isoformat()])

    filename = f"ata-{bingo.name}-rodada-{round_.number}.csv".replace(" ", "-").lower()
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@main_bp.get("/sala/<public_id>")
def public_bingo(public_id):
    bingo = Bingo.query.filter_by(public_id=public_id).first_or_404()
    return render_template("bingos/public.html", bingo=bingo, numbers=range(1, 76))


@main_bp.get("/api/salas/<public_id>")
def public_bingo_state(public_id):
    bingo = Bingo.query.filter_by(public_id=public_id).first_or_404()
    round_ = bingo.active_round
    return jsonify(
        {
            "name": bingo.name,
            "round": round_.number if round_ else None,
            "status": round_.status if round_ else "waiting",
            "last_number": round_.last_number if round_ else None,
            "last_call": (
                f"{bingo_letter(round_.last_number)}-{round_.last_number}"
                if round_ and round_.last_number
                else None
            ),
            "drawn_numbers": round_.drawn_numbers if round_ else [],
            "remaining_count": 75 - len(round_.draws) if round_ else 75,
        }
    )
