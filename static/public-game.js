const body = document.body;
const stateUrl = body.dataset.stateUrl;
const ball = document.getElementById("public-ball");
let ballLetter = document.getElementById("public-letter");
let ballNumber = document.getElementById("public-number");
const roundLabel = document.getElementById("public-round");
const message = document.getElementById("public-message");
const remainingCount = document.getElementById("remaining-count");
const fullscreenButton = document.getElementById("fullscreen-button");
const soundButton = document.getElementById("sound-button");
let previousNumber = null;
let voiceEnabled = false;

function ensureBallLayout() {
    if (ballLetter && ballNumber) return;

    ball.replaceChildren();
    ballLetter = document.createElement("small");
    ballLetter.id = "public-letter";
    ballNumber = document.createElement("span");
    ballNumber.id = "public-number";
    ballNumber.textContent = "—";
    ball.append(ballLetter, ballNumber);
}

ensureBallLayout();

function speakCall(call) {
    if (!voiceEnabled || !call || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(call.replace("-", ", número "));
    utterance.lang = "pt-BR";
    utterance.rate = 0.85;
    window.speechSynthesis.speak(utterance);
}

soundButton.addEventListener("click", () => {
    voiceEnabled = !voiceEnabled;
    soundButton.textContent = voiceEnabled ? "Voz ativada" : "Ativar voz";
});

fullscreenButton.addEventListener("click", async () => {
    if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
    } else {
        await document.exitFullscreen();
    }
});

async function refreshGame() {
    try {
        const response = await fetch(stateUrl, {headers: {"Accept": "application/json"}});
        if (!response.ok) throw new Error("Falha ao consultar a rodada");

        const state = await response.json();
        const drawn = new Set(state.drawn_numbers);

        document.querySelectorAll("[data-number]").forEach((element) => {
            element.classList.toggle("is-drawn", drawn.has(Number(element.dataset.number)));
        });

        remainingCount.textContent = `${state.remaining_count} números restantes`;

        if (["active", "paused", "checking"].includes(state.status)) {
            roundLabel.textContent = `Rodada ${state.round} · ${drawn.size}/75`;
            if (state.status === "checking") {
                message.textContent = "BINGO anunciado — conferência em andamento.";
                document.body.classList.add("is-checking");
            } else if (state.status === "paused") {
                message.textContent = "Rodada pausada pelo organizador.";
                document.body.classList.remove("is-checking");
            } else {
                message.textContent = drawn.size ? "Acompanhe os números já sorteados." : "Aguardando o primeiro sorteio.";
                document.body.classList.remove("is-checking");
            }
            ballLetter.textContent = state.last_call ? state.last_call.split("-")[0] : "";
            ballNumber.textContent = state.last_number ?? "—";

            if (state.last_number && state.last_number !== previousNumber) {
                ball.classList.remove("ball-pop");
                void ball.offsetWidth;
                ball.classList.add("ball-pop");
                speakCall(state.last_call);
            }
            previousNumber = state.last_number;
        } else {
            roundLabel.textContent = "Aguardando rodada";
            message.textContent = "Aguardando o organizador iniciar a rodada.";
            ballLetter.textContent = "";
            ballNumber.textContent = "—";
            previousNumber = null;
            document.body.classList.remove("is-checking");
        }
    } catch (error) {
        console.error("Falha ao atualizar a tela pública:", error);
        message.textContent = "Reconectando à rodada…";
    }
}

refreshGame();
setInterval(refreshGame, 2000);
