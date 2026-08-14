const API_BASE = "https://vaanidoc-vwtv.onrender.com";

const submitButton = document.getElementById("submitButton");
const voiceButton = document.getElementById("voiceButton");
const symptomsInput = document.getElementById("symptoms");
const languageInput = document.getElementById("language");
const resultSection = document.getElementById("resultSection");
const resultLanguage = document.getElementById("resultLanguage");
const resultSymptoms = document.getElementById("resultSymptoms");
const resultDuration = document.getElementById("resultDuration");
const resultCategory = document.getElementById("resultCategory");
const voiceStatus = document.getElementById("voiceStatus");
const statusBanner = document.getElementById("statusBanner");
const sessionIdDisplay = document.getElementById("sessionIdDisplay");
const clockDisplay = document.getElementById("clockDisplay");
const resultSummary = document.getElementById("resultSummary");

function updateClock() {
    if (!clockDisplay) return;

    const now = new Date();

    clockDisplay.textContent = now.toLocaleString("en-IN", {
        weekday: "short",
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
}

updateClock();
setInterval(updateClock, 1000);

function setStatus(message, isError = false) {
    if (!statusBanner) return;

    statusBanner.textContent = message;
    statusBanner.classList.remove("hidden");
    statusBanner.classList.toggle("status-error", isError);
}

submitButton.addEventListener("click", async function () {
    const language = languageInput.value;
    const symptoms_text = symptomsInput.value.trim();

    if (!symptoms_text) {
        alert("Please describe your symptoms first.");
        return;
    }

    submitButton.disabled = true;
    submitButton.textContent = "Processing...";
    setStatus("Processing your symptoms...", false);

    try {
        const response = await fetch(`${API_BASE}/api/intake`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                language: language,
                symptoms_text: symptoms_text
            })
        });

        const responseText = await response.text();

        let data;

        try {
            data = JSON.parse(responseText);
        } catch {
            throw new Error(
                `Backend returned an invalid response: ${responseText}`
            );
        }

        if (!response.ok) {
            throw new Error(
                data.detail || `Backend error: ${response.status}`
            );
        }

        resultLanguage.textContent = data.language || language;

        if (Array.isArray(data.symptoms)) {
            resultSymptoms.textContent = data.symptoms.join(", ");
        } else {
            resultSymptoms.textContent =
                data.symptoms || "Symptoms not detected";
        }

        resultDuration.textContent =
            data.duration || "Not specified";

        resultCategory.textContent =
            data.category || "General";

        if (resultSummary) {
            resultSummary.textContent =
                data.summary || "AI summary not available.";
        }

        if (sessionIdDisplay) {
            sessionIdDisplay.textContent =
                data.session_id || "N/A";
        }

        resultSection.classList.remove("hidden");

        resultSection.scrollIntoView({
            behavior: "smooth"
        });

        setStatus("Symptoms processed successfully.", false);

    } catch (error) {
        console.error("Backend error:", error);

        setStatus(
            `Could not process your submission: ${error.message}`,
            true
        );
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Continue";
    }
});

voiceButton.addEventListener("click", function () {

    if (
        !("SpeechRecognition" in window) &&
        !("webkitSpeechRecognition" in window)
    ) {
        alert(
            "Speech recognition is not supported in this browser. Please use Google Chrome."
        );
        return;
    }

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    const recognition = new SpeechRecognition();

    recognition.lang = getSpeechLanguage(languageInput.value);
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    voiceStatus.textContent = "Listening...";
    voiceButton.textContent = "🎙️ Listening...";
    voiceButton.disabled = true;

    try {
        recognition.start();
    } catch (error) {
        console.error(error);

        voiceStatus.textContent = "Microphone could not start.";
        voiceButton.textContent = "🎤 Speak";
        voiceButton.disabled = false;
    }

    recognition.onresult = function (event) {

        const transcript =
            event.results[0][0].transcript;

        symptomsInput.value = transcript;

        voiceStatus.textContent =
            "Speech captured successfully.";

        voiceButton.textContent = "🎤 Speak";
        voiceButton.disabled = false;
    };

    recognition.onerror = function (event) {

        console.error(
            "Speech recognition error:",
            event.error
        );

        if (event.error === "not-allowed") {
            voiceStatus.textContent =
                "Microphone permission denied. Please allow microphone access.";
        } else if (event.error === "no-speech") {
            voiceStatus.textContent =
                "No speech detected. Please try again.";
        } else if (event.error === "network") {
            voiceStatus.textContent =
                "Speech recognition network error.";
        } else {
            voiceStatus.textContent =
                "Could not understand speech. Please try again.";
        }

        voiceButton.textContent = "🎤 Speak";
        voiceButton.disabled = false;
    };

    recognition.onend = function () {
        voiceButton.textContent = "🎤 Speak";
        voiceButton.disabled = false;
    };
});

function getSpeechLanguage(language) {

    const languages = {
        English: "en-IN",
        Hindi: "hi-IN",
        Gujarati: "gu-IN",
        Marathi: "mr-IN",
        Bengali: "bn-IN",
        Tamil: "ta-IN",
        Telugu: "te-IN",
        Kannada: "kn-IN",
        Malayalam: "ml-IN",
        Punjabi: "pa-IN"
    };

    return languages[language] || "en-IN";
}
