const form = document.getElementById("predictionForm");
const button = document.getElementById("predictButton");

const loading = document.getElementById("loading");
const result = document.getElementById("result");
const errorBox = document.getElementById("error");

const predictedPrice = document.getElementById("predictedPrice");
const comparison = document.getElementById("comparison");
const recommendation = document.getElementById("recommendation");
const reason = document.getElementById("reason");

const resetButton = document.getElementById("resetButton");

function formatPrice(value) {
    return new Intl.NumberFormat("en-IN", {
        maximumFractionDigits: 2
    }).format(value);
}

function hideMessages() {
    result.classList.add("hidden");
    errorBox.classList.add("hidden");
    errorBox.textContent = "";
}

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    hideMessages();

    const formData = new FormData(form);

    const data = {
        Brand: formData.get("Brand"),
        Year: Number(formData.get("Year")),
        Kilometers_Driven: Number(formData.get("Kilometers_Driven")),
        Engine_CC: Number(formData.get("Engine_CC")),
        Mileage_Kmpl: Number(formData.get("Mileage_Kmpl")),
        Fuel_Type: formData.get("Fuel_Type"),
        Transmission: formData.get("Transmission"),
        Owner: formData.get("Owner"),
        asking_price: Number(formData.get("asking_price"))
    };

    button.disabled = true;
    button.textContent = "Predicting...";
    loading.classList.remove("hidden");

    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        const payload = await response.json();

        if (!response.ok) {
            throw new Error(payload.error || "Prediction failed.");
        }

        predictedPrice.textContent = formatPrice(
            payload.predicted_price
        );

        const difference =
            payload.asking_price - payload.predicted_price;

        const percentage = Math.abs(difference) /
            Math.abs(payload.predicted_price) * 100;

        if (difference > 0) {
            comparison.textContent =
                `The asking price is ${formatPrice(difference)} ` +
                `above the estimated value (${percentage.toFixed(1)}% higher).`;
        } else if (difference < 0) {
            comparison.textContent =
                `The asking price is ${formatPrice(Math.abs(difference))} ` +
                `below the estimated value (${percentage.toFixed(1)}% lower).`;
        } else {
            comparison.textContent =
                "The asking price matches the estimated value.";
        }

        recommendation.textContent = payload.recommendation;

        recommendation.className = "recommendation";

        if (payload.recommendation === "BUY") {
            recommendation.classList.add("buy");
        } else if (payload.recommendation === "NEGOTIATE") {
            recommendation.classList.add("negotiate");
        } else if (payload.recommendation === "REVIEW") {
            recommendation.classList.add("review");
        } else {
            recommendation.classList.add("avoid");
        }

        reason.textContent = payload.reason;

        result.classList.remove("hidden");

        result.scrollIntoView({
            behavior: "smooth",
            block: "nearest"
        });

    } catch (error) {
        errorBox.textContent =
            error.message || "Unable to connect to the server.";

        errorBox.classList.remove("hidden");

    } finally {
        loading.classList.add("hidden");
        button.disabled = false;
        button.innerHTML = 'Predict Car Price <span>→</span>';
    }
});

resetButton.addEventListener("click", function () {
    form.reset();
    hideMessages();

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
});