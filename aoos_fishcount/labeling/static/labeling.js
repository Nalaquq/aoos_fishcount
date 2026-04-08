// Salmon Labeling Tool — Canvas-based bounding box annotation

const SPECIES = {};
const COLORS = {};

// Parse species data from DOM
document.querySelectorAll(".species-btn").forEach(btn => {
    const id = parseInt(btn.dataset.classId);
    SPECIES[id] = btn.textContent.trim().split("\n")[0].trim();
    COLORS[id] = btn.querySelector(".color-swatch").style.background;
});

// --- State ---

let images = [];
let currentIndex = 0;
let annotations = [];
let selectedClassId = 0;
let selectedAnnId = null;
let isDirty = false;

// Drawing state
let isDrawing = false;
let drawStart = null;
let drawCurrent = null;

// Resize state
let isResizing = false;
let resizeHandle = null;  // "nw", "ne", "sw", "se"
let resizeAnn = null;
let resizeStart = null;

// Move state
let isMoving = false;
let moveAnn = null;
let moveOffset = null;

// Image and canvas
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const img = new Image();
let imgScale = 1;
let imgOffsetX = 0;
let imgOffsetY = 0;

// DOM elements
const annotationsList = document.getElementById("annotations-list");
const noAnnotations = document.getElementById("no-annotations");
const imageCounter = document.getElementById("image-counter");
const statusMsg = document.getElementById("status-message");

// --- Init ---

async function init() {
    const resp = await fetch("/api/images");
    const data = await resp.json();
    images = data.images;

    if (images.length === 0) {
        showStatus("No images found in input directory.", "error");
        return;
    }

    // Select first species button
    document.querySelector(".species-btn").classList.add("active");

    await loadImage(0);
    updateProgress();
}

// --- Image loading ---

async function loadImage(index) {
    if (index < 0 || index >= images.length) return;

    // Auto-save if dirty
    if (isDirty) await saveAnnotations();

    currentIndex = index;
    const filename = images[currentIndex];

    imageCounter.textContent = `${currentIndex + 1} / ${images.length}`;

    // Load annotations
    const resp = await fetch(`/api/annotations/${encodeURIComponent(filename)}`);
    const data = await resp.json();
    annotations = data.annotations || [];
    selectedAnnId = null;
    isDirty = false;

    // Load image
    img.onload = () => {
        fitCanvas();
        render();
        renderAnnotationsList();
    };
    img.src = `/api/image/${encodeURIComponent(filename)}`;
}

function fitCanvas() {
    const container = document.getElementById("canvas-container");
    const cw = container.clientWidth;
    const ch = container.clientHeight;

    const scaleX = cw / img.naturalWidth;
    const scaleY = ch / img.naturalHeight;
    imgScale = Math.min(scaleX, scaleY, 1);

    canvas.width = Math.floor(img.naturalWidth * imgScale);
    canvas.height = Math.floor(img.naturalHeight * imgScale);
    imgOffsetX = 0;
    imgOffsetY = 0;
}

// --- Rendering ---

function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    // Draw existing annotations
    for (const ann of annotations) {
        drawBox(ann, ann.id === selectedAnnId);
    }

    // Draw in-progress box
    if (isDrawing && drawStart && drawCurrent) {
        const x = Math.min(drawStart.x, drawCurrent.x);
        const y = Math.min(drawStart.y, drawCurrent.y);
        const w = Math.abs(drawCurrent.x - drawStart.x);
        const h = Math.abs(drawCurrent.y - drawStart.y);
        ctx.strokeStyle = COLORS[selectedClassId];
        ctx.lineWidth = 2;
        ctx.setLineDash([6, 3]);
        ctx.strokeRect(x, y, w, h);
        ctx.setLineDash([]);
    }
}

function drawBox(ann, selected) {
    const x = ann.x * canvas.width;
    const y = ann.y * canvas.height;
    const w = ann.w * canvas.width;
    const h = ann.h * canvas.height;
    const color = COLORS[ann.class_id];

    // Fill
    ctx.fillStyle = color + "22";
    ctx.fillRect(x, y, w, h);

    // Stroke
    ctx.strokeStyle = color;
    ctx.lineWidth = selected ? 3 : 2;
    ctx.strokeRect(x, y, w, h);

    // Label
    const label = SPECIES[ann.class_id] || `class ${ann.class_id}`;
    ctx.font = "bold 13px sans-serif";
    const textW = ctx.measureText(label).width + 8;
    ctx.fillStyle = color;
    ctx.fillRect(x, y - 20, textW, 20);
    ctx.fillStyle = "#fff";
    ctx.fillText(label, x + 4, y - 6);

    // Resize handles for selected box
    if (selected) {
        const handleSize = 8;
        const handles = [
            [x, y], [x + w, y],
            [x, y + h], [x + w, y + h],
        ];
        ctx.fillStyle = "#fff";
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        for (const [hx, hy] of handles) {
            ctx.fillRect(hx - handleSize/2, hy - handleSize/2, handleSize, handleSize);
            ctx.strokeRect(hx - handleSize/2, hy - handleSize/2, handleSize, handleSize);
        }
    }
}

// --- Annotations list ---

function renderAnnotationsList() {
    annotationsList.innerHTML = "";
    noAnnotations.style.display = annotations.length ? "none" : "block";

    for (const ann of annotations) {
        const li = document.createElement("li");
        if (ann.id === selectedAnnId) li.classList.add("selected");

        const swatch = document.createElement("span");
        swatch.className = "color-swatch";
        swatch.style.background = COLORS[ann.class_id];
        li.appendChild(swatch);

        const text = document.createElement("span");
        text.textContent = SPECIES[ann.class_id] || `class ${ann.class_id}`;
        li.appendChild(text);

        const del = document.createElement("button");
        del.className = "ann-delete";
        del.textContent = "\u00d7";
        del.title = "Delete annotation";
        del.addEventListener("click", (e) => {
            e.stopPropagation();
            deleteAnnotation(ann.id);
        });
        li.appendChild(del);

        li.addEventListener("click", () => {
            selectedAnnId = ann.id;
            render();
            renderAnnotationsList();
        });

        annotationsList.appendChild(li);
    }
}

// --- Mouse handling ---

function canvasToNorm(px, py) {
    return { x: px / canvas.width, y: py / canvas.height };
}

function getMousePos(e) {
    const rect = canvas.getBoundingClientRect();
    return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
    };
}

function hitTestHandles(px, py) {
    if (!selectedAnnId) return null;
    const ann = annotations.find(a => a.id === selectedAnnId);
    if (!ann) return null;

    const x = ann.x * canvas.width;
    const y = ann.y * canvas.height;
    const w = ann.w * canvas.width;
    const h = ann.h * canvas.height;
    const r = 10;

    const corners = {
        "nw": [x, y],
        "ne": [x + w, y],
        "sw": [x, y + h],
        "se": [x + w, y + h],
    };

    for (const [handle, [cx, cy]] of Object.entries(corners)) {
        if (Math.abs(px - cx) < r && Math.abs(py - cy) < r) {
            return { handle, ann };
        }
    }
    return null;
}

function hitTestBox(px, py) {
    const nx = px / canvas.width;
    const ny = py / canvas.height;

    // Reverse order so topmost (last drawn) is hit first
    for (let i = annotations.length - 1; i >= 0; i--) {
        const ann = annotations[i];
        if (nx >= ann.x && nx <= ann.x + ann.w &&
            ny >= ann.y && ny <= ann.y + ann.h) {
            return ann;
        }
    }
    return null;
}

canvas.addEventListener("mousedown", (e) => {
    if (e.button !== 0) return;
    const pos = getMousePos(e);

    // Check resize handles first
    const handleHit = hitTestHandles(pos.x, pos.y);
    if (handleHit) {
        isResizing = true;
        resizeHandle = handleHit.handle;
        resizeAnn = handleHit.ann;
        resizeStart = { ...pos };
        return;
    }

    // Check if clicking an existing box
    const boxHit = hitTestBox(pos.x, pos.y);
    if (boxHit) {
        // If clicking already selected box, start moving
        if (boxHit.id === selectedAnnId) {
            isMoving = true;
            moveAnn = boxHit;
            moveOffset = {
                x: pos.x / canvas.width - boxHit.x,
                y: pos.y / canvas.height - boxHit.y,
            };
            return;
        }
        // Otherwise select it
        selectedAnnId = boxHit.id;
        render();
        renderAnnotationsList();
        return;
    }

    // Start new drawing
    selectedAnnId = null;
    isDrawing = true;
    drawStart = { ...pos };
    drawCurrent = { ...pos };
    renderAnnotationsList();
});

canvas.addEventListener("mousemove", (e) => {
    const pos = getMousePos(e);

    if (isDrawing) {
        drawCurrent = { ...pos };
        render();
        return;
    }

    if (isResizing && resizeAnn) {
        const nx = pos.x / canvas.width;
        const ny = pos.y / canvas.height;

        const ann = resizeAnn;
        const right = ann.x + ann.w;
        const bottom = ann.y + ann.h;

        if (resizeHandle.includes("w")) { ann.w = right - nx; ann.x = nx; }
        if (resizeHandle.includes("e")) { ann.w = nx - ann.x; }
        if (resizeHandle.includes("n")) { ann.h = bottom - ny; ann.y = ny; }
        if (resizeHandle.includes("s")) { ann.h = ny - ann.y; }

        // Prevent negative dimensions
        if (ann.w < 0) { ann.x += ann.w; ann.w = Math.abs(ann.w); }
        if (ann.h < 0) { ann.y += ann.h; ann.h = Math.abs(ann.h); }

        isDirty = true;
        render();
        return;
    }

    if (isMoving && moveAnn) {
        moveAnn.x = Math.max(0, Math.min(1 - moveAnn.w, pos.x / canvas.width - moveOffset.x));
        moveAnn.y = Math.max(0, Math.min(1 - moveAnn.h, pos.y / canvas.height - moveOffset.y));
        isDirty = true;
        render();
        return;
    }

    // Update cursor
    const handleHit = hitTestHandles(pos.x, pos.y);
    if (handleHit) {
        const cursors = { nw: "nw-resize", ne: "ne-resize", sw: "sw-resize", se: "se-resize" };
        canvas.style.cursor = cursors[handleHit.handle];
    } else if (hitTestBox(pos.x, pos.y)?.id === selectedAnnId && selectedAnnId) {
        canvas.style.cursor = "move";
    } else {
        canvas.style.cursor = "crosshair";
    }
});

canvas.addEventListener("mouseup", (e) => {
    if (isDrawing) {
        isDrawing = false;
        const pos = getMousePos(e);

        const x1 = Math.min(drawStart.x, pos.x) / canvas.width;
        const y1 = Math.min(drawStart.y, pos.y) / canvas.height;
        const x2 = Math.max(drawStart.x, pos.x) / canvas.width;
        const y2 = Math.max(drawStart.y, pos.y) / canvas.height;
        const w = x2 - x1;
        const h = y2 - y1;

        // Ignore tiny boxes (accidental clicks)
        if (w > 0.005 && h > 0.005) {
            const id = Math.random().toString(36).substring(2, 10);
            annotations.push({
                id,
                class_id: selectedClassId,
                x: x1, y: y1, w, h,
            });
            selectedAnnId = id;
            isDirty = true;
            renderAnnotationsList();
        }

        drawStart = null;
        drawCurrent = null;
        render();
        return;
    }

    if (isResizing) {
        isResizing = false;
        resizeHandle = null;
        resizeAnn = null;
        resizeStart = null;
        return;
    }

    if (isMoving) {
        isMoving = false;
        moveAnn = null;
        moveOffset = null;
        return;
    }
});

// --- API calls ---

async function saveAnnotations() {
    const filename = images[currentIndex];
    const resp = await fetch(`/api/annotations/${encodeURIComponent(filename)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ annotations }),
    });
    const data = await resp.json();
    isDirty = false;
    showStatus(`Saved ${data.count} annotation(s)`, "success");
}

async function deleteAnnotation(id) {
    annotations = annotations.filter(a => a.id !== id);
    if (selectedAnnId === id) selectedAnnId = null;
    isDirty = true;
    render();
    renderAnnotationsList();
}

async function markProgress(status) {
    const filename = images[currentIndex];
    await fetch(`/api/progress/${encodeURIComponent(filename)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
    });
    updateProgress();
}

async function updateProgress() {
    const resp = await fetch("/api/progress");
    const data = await resp.json();
    const pct = data.total > 0 ? ((data.completed / data.total) * 100).toFixed(0) : 0;
    document.getElementById("progress-fill").style.width = `${pct}%`;
    document.getElementById("progress-text").textContent =
        `${data.completed} done, ${data.skipped} skipped, ${data.remaining} remaining`;
}

async function exportYolo() {
    if (isDirty) await saveAnnotations();
    const resp = await fetch("/api/export", { method: "POST" });
    const data = await resp.json();
    showStatus(`Exported ${data.count} labeled images to YOLO format`, "success");
}

// --- Status message ---

let statusTimeout = null;
function showStatus(msg, type) {
    statusMsg.textContent = msg;
    statusMsg.className = `visible ${type}`;
    clearTimeout(statusTimeout);
    statusTimeout = setTimeout(() => {
        statusMsg.className = "";
    }, 3000);
}

// --- Button handlers ---

document.querySelectorAll(".species-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".species-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        selectedClassId = parseInt(btn.dataset.classId);

        // If a box is selected, change its class
        if (selectedAnnId) {
            const ann = annotations.find(a => a.id === selectedAnnId);
            if (ann) {
                ann.class_id = selectedClassId;
                isDirty = true;
                render();
                renderAnnotationsList();
            }
        }
    });
});

document.getElementById("btn-prev").addEventListener("click", () => {
    if (currentIndex > 0) loadImage(currentIndex - 1);
});

document.getElementById("btn-next").addEventListener("click", () => {
    if (currentIndex < images.length - 1) loadImage(currentIndex + 1);
});

document.getElementById("btn-save").addEventListener("click", saveAnnotations);

document.getElementById("btn-skip").addEventListener("click", async () => {
    await markProgress("skipped");
    if (currentIndex < images.length - 1) loadImage(currentIndex + 1);
});

document.getElementById("btn-done").addEventListener("click", async () => {
    await saveAnnotations();
    await markProgress("completed");
    if (currentIndex < images.length - 1) loadImage(currentIndex + 1);
});

document.getElementById("btn-export").addEventListener("click", exportYolo);

// --- Keyboard shortcuts ---

document.addEventListener("keydown", (e) => {
    // Don't capture if typing in an input
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

    // 1-5: select species
    if (e.key >= "1" && e.key <= "5") {
        const classId = parseInt(e.key) - 1;
        document.querySelectorAll(".species-btn").forEach(b => b.classList.remove("active"));
        const btn = document.querySelector(`.species-btn[data-class-id="${classId}"]`);
        if (btn) {
            btn.classList.add("active");
            selectedClassId = classId;
            // Change selected box class
            if (selectedAnnId) {
                const ann = annotations.find(a => a.id === selectedAnnId);
                if (ann) {
                    ann.class_id = classId;
                    isDirty = true;
                    render();
                    renderAnnotationsList();
                }
            }
        }
        return;
    }

    // Arrow keys: navigate
    if (e.key === "ArrowLeft") {
        e.preventDefault();
        if (currentIndex > 0) loadImage(currentIndex - 1);
        return;
    }
    if (e.key === "ArrowRight") {
        e.preventDefault();
        if (currentIndex < images.length - 1) loadImage(currentIndex + 1);
        return;
    }

    // Ctrl+S: save
    if (e.key === "s" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        saveAnnotations();
        return;
    }

    // S (no modifier): skip
    if (e.key === "s" && !e.ctrlKey && !e.metaKey) {
        document.getElementById("btn-skip").click();
        return;
    }

    // Enter: done & next
    if (e.key === "Enter") {
        e.preventDefault();
        document.getElementById("btn-done").click();
        return;
    }

    // Delete/Backspace: remove selected box
    if ((e.key === "Delete" || e.key === "Backspace") && selectedAnnId) {
        e.preventDefault();
        deleteAnnotation(selectedAnnId);
        return;
    }

    // Escape: cancel drawing / deselect
    if (e.key === "Escape") {
        if (isDrawing) {
            isDrawing = false;
            drawStart = null;
            drawCurrent = null;
            render();
        }
        selectedAnnId = null;
        render();
        renderAnnotationsList();
        return;
    }
});

// --- Window resize ---

window.addEventListener("resize", () => {
    if (img.naturalWidth) {
        fitCanvas();
        render();
    }
});

// Auto-save on page unload
window.addEventListener("beforeunload", (e) => {
    if (isDirty) {
        saveAnnotations();
        e.preventDefault();
        e.returnValue = "";
    }
});

// --- Start ---

init();
