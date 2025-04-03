// ---------------- Text Effect ---------------------
let currentFaceIndex = 0;
const faces = ["front", "bottom", "back", "top"];
const textContainer = document.querySelector(".left-text");
const images = document.querySelectorAll(".image");
let rotationInProgress = false;
let firstCycleCompleted = false;

document.body.style.overflowY = "hidden";

function updateImages(faceIndex) {
    images.forEach((img) => {
        img.classList.remove("pulsate");
    });

    const imageToShow = images[faceIndex];
    if (imageToShow) {
        imageToShow.classList.add("in-view");

        if (firstCycleCompleted) {
            imageToShow.classList.add("pulsate");
        }
    }
}

window.addEventListener("wheel", (event) => {
    if (rotationInProgress) return;

    rotationInProgress = true; 
    if (event.deltaY > 0) {
        // Scroll down - Move to the next face
        currentFaceIndex = (currentFaceIndex + 1) % faces.length;
    } else {
        // Scroll up - Move to the previous face
        currentFaceIndex = (currentFaceIndex - 1 + faces.length) % faces.length;
    }

    const newAngle = -currentFaceIndex * 90;
    textContainer.style.transform = `rotateX(${newAngle}deg)`;

    updateImages(currentFaceIndex);

    if (currentFaceIndex === 0) {
        firstCycleCompleted = true;
        document.body.style.overflowY = "auto"; // Unlock scroll after first rotation
    }

    // Unlock rotation after transition completes
    setTimeout(() => {
        rotationInProgress = false;
    }, 1000); 
});

window.addEventListener("DOMContentLoaded", () => {
    const image1 = document.querySelector(".image1");
    image1.classList.add("in-view");
});

// ------------------------ Find Turfs ------------------------------
document.addEventListener("DOMContentLoaded", () => {
    const turfsContainer = document.querySelector(".turfs");
    const leftArrow = document.querySelector(".left-arrow");
    const rightArrow = document.querySelector(".right-arrow");

    // Update arrow states
    function updateArrows() {
        // Disable the left arrow if at the start of the container
        leftArrow.disabled = turfsContainer.scrollLeft === 0;

        // Disable the right arrow if at the end of the container
        rightArrow.disabled = turfsContainer.scrollLeft + turfsContainer.clientWidth >= turfsContainer.scrollWidth - 1;
    }

    // Scroll right
    rightArrow.addEventListener("click", () => {
        turfsContainer.scrollBy({ left: 300, behavior: "smooth" });
        setTimeout(updateArrows, 500); // Update arrows after scrolling
    });

    // Scroll left
    leftArrow.addEventListener("click", () => {
        turfsContainer.scrollBy({ left: -300, behavior: "smooth" });
        setTimeout(updateArrows, 500); // Update arrows after scrolling
    });

    // Check arrow states on load
    updateArrows();
});