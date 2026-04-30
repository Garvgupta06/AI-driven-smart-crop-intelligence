const heroLines = [
    "This website helps monitor soil moisture, temperature, and humidity using live Blynk data.",
    "Smart irrigation helps reduce water waste and supports healthier plant growth.",
    "Live sensor values make it easier to understand field conditions from one dashboard.",
    "The system helps users decide when plants need water and when irrigation can wait.",
    "Login to open the dashboard and view real-time readings from the irrigation system."
];

const heroImages = [
    "https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&w=1600&q=80"
];

const heroSection = document.querySelector(".hero");
const heroText = document.getElementById("hero-rotating-text");
let heroLineIndex = 0;
let heroImageIndex = 0;

function updateHeroText() {
    if (!heroText) {
        return;
    }

    heroLineIndex = (heroLineIndex + 1) % heroLines.length;
    heroText.innerText = heroLines[heroLineIndex];
}

setInterval(updateHeroText, 5000);

function updateHeroImage() {
    if (!heroSection) {
        return;
    }

    heroImageIndex = (heroImageIndex + 1) % heroImages.length;
    heroSection.style.setProperty("--hero-image", `url("${heroImages[heroImageIndex]}")`);
}

setInterval(updateHeroImage, 10000);
