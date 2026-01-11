const canvas = document.getElementById('wall');
const ctx = canvas.getContext('2d');

let notes = [];
let previousDataStr = "";

// Camera
let camera = { x: 0, y: 0, zoom: 1 };
let isDragging = false;
let isDraggingNote = false;
let draggedNote = null;
let lastMouse = { x: 0, y: 0 };
let dragStart = { x: 0, y: 0 };
let dragOffset = { x: 0, y: 0 };
let hasDragged = false;

// Audio State
let currentAudio = null; // Currently playing audio object
let currentPlayingNoteId = null;

// UI State
const ui = {
    modal: document.getElementById('note-modal'),
    addBtn: document.getElementById('add-btn'),
    saveBtn: document.getElementById('save-btn'),
    cancelBtn: document.getElementById('cancel-btn'),
    
    // Tabs
    tabText: document.getElementById('tab-text'),
    tabMusic: document.getElementById('tab-music'),
    sectText: document.getElementById('section-text'),
    sectMusic: document.getElementById('section-music'),
    
    // Inputs
    inputText: document.getElementById('note-text'),
    inputMusicFile: document.getElementById('music-file'),
    inputMusicThumb: document.getElementById('music-thumb'),
    inputMusicTitle: document.getElementById('music-title'),
    fileLabel: document.getElementById('file-name-display'),
    thumbLabel: document.getElementById('thumb-name-display')
};

let activeTab = 'text'; // 'text' or 'music'

// Configuration
const BASE_WIDTH = 220;
const BASE_HEIGHT = 180;
const MUSIC_CARD_HEIGHT = 260; // Taller for music cards
const EXPANDED_WIDTH = 300; 
const PADDING = 60; 

const COLORS = [
    '#fef68a', // Yellow
    '#bbf7d0', // Green
    '#bfdbfe', // Blue
    '#fecaca', // Red
    '#fed7aa', // Orange
    '#ddd6fe'  // Purple
];

// --- Initialization ---
function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    draw();
}
window.addEventListener('resize', resize);
resize();

// --- Input Handling ---
canvas.addEventListener('mousedown', e => {
    lastMouse = { x: e.clientX, y: e.clientY };
    dragStart = { x: e.clientX, y: e.clientY };
    hasDragged = false;
    
    const hit = findNoteAt(e.clientX, e.clientY);
    if (hit) {
        // Check for DELETE Button Click
        if (checkButtonHit(hit.note, e.clientX, e.clientY, 'delete')) {
            deleteNote(hit.index);
            return;
        }

        // Check for PLAY/PAUSE for Music
        if (hit.note.type === 'music') {
             if (checkButtonHit(hit.note, e.clientX, e.clientY, 'play')) {
                toggleMusic(hit.note);
                return;
             }
        }

        // Start Dragging Note
        isDraggingNote = true;
        draggedNote = hit.note;
        draggedNote.zIndex = 100;
        
        // Calculate World Mouse
        const wx = (e.clientX - camera.x) / camera.zoom;
        const wy = (e.clientY - camera.y) / camera.zoom;

        dragOffset = {
            x: wx - hit.note.x,
            y: wy - hit.note.y
        };
        canvas.style.cursor = 'move';
    } else {
        isDragging = true;
        canvas.style.cursor = 'grabbing';
    }
});

canvas.addEventListener('mousemove', e => {
    lastMouse = { x: e.clientX, y: e.clientY };

    if (isDraggingNote && draggedNote) {
        hasDragged = true;
        const wx = (e.clientX - camera.x) / camera.zoom;
        const wy = (e.clientY - camera.y) / camera.zoom;
        draggedNote.x = wx - dragOffset.x;
        draggedNote.y = wy - dragOffset.y;
    }
    else if (isDragging) {
        hasDragged = true;
        camera.x += e.movementX;
        camera.y += e.movementY;
    }
});

canvas.addEventListener('mouseup', e => {
    isDraggingNote = false;
    draggedNote = null;
    isDragging = false;
    canvas.style.cursor = 'grab';
    saveData();

    // Check for Click (Expand Text Note)
    const dist = Math.hypot(e.clientX - dragStart.x, e.clientY - dragStart.y);
    if (dist < 5) {
        handleNoteClick(e.clientX, e.clientY);
    }
});

canvas.addEventListener('wheel', e => {
    e.preventDefault();
    const zoomSensitivity = 0.001;
    let newZoom = camera.zoom - e.deltaY * zoomSensitivity;
    newZoom = Math.max(0.2, Math.min(2.0, newZoom)); 

    const mouseX = e.clientX;
    const mouseY = e.clientY;
    const wx = (mouseX - camera.x) / camera.zoom;
    const wy = (mouseY - camera.y) / camera.zoom;

    camera.zoom = newZoom;
    camera.x = mouseX - wx * newZoom;
    camera.y = mouseY - wy * newZoom;
}, { passive: false });

function findNoteAt(screenX, screenY) {
    const wx = (screenX - camera.x) / camera.zoom;
    const wy = (screenY - camera.y) / camera.zoom;
    
    // Check top-most first (reverse order)
    for (let i = notes.length - 1; i >= 0; i--) {
        const n = notes[i];
        if (wx > n.x && wx < n.x + n.w &&
            wy > n.y && wy < n.y + n.h) {
            return { note: n, index: i };
        }
    }
    return null;
}

function checkButtonHit(note, screenX, screenY, btnType) {
    const wx = (screenX - camera.x) / camera.zoom;
    const wy = (screenY - camera.y) / camera.zoom;
    
    const cx = note.x + note.w/2;
    const cy = note.y + note.h/2; 

    if (btnType === 'delete') {
        // T-Right corner
        const dx = cx + note.w/2 - 15;
        const dy = cy - note.h/2 + 15;
        return Math.hypot(wx - dx, wy - dy) < 15;
    }
    
    if (btnType === 'play') {
        // New Card Layout Play Button Position:
        // Bottom Right area
        const playX = cx + note.w/2 - 35;
        const playY = cy + note.h/2 - 35;
        
        return Math.hypot(wx - playX, wy - playY) < 25; 
    }
    
    return false;
}

function handleNoteClick(screenX, screenY) {
    const hit = findNoteAt(screenX, screenY);
    if (hit) {
        const n = hit.note;
        if (n.type === 'music') return; // Don't expand music notes

        n.expanded = !n.expanded;
        if (n.expanded) {
            n.w = EXPANDED_WIDTH;
            ctx.font = "24px 'Kalam', cursive";
            const lines = wrapText(n.text || "", n.w - 40);
            const textH = lines.length * 30;
            n.h = Math.max(BASE_HEIGHT, textH + 80); 
        } else {
            n.w = BASE_WIDTH;
            n.h = BASE_HEIGHT;
        }
    }
}

// --- UI Logic ---
ui.addBtn.addEventListener('click', () => {
    ui.modal.classList.remove('hidden');
    // Reset UI
    switchTab('text');
    ui.inputText.value = "";
    ui.inputMusicTitle.value = "";
    ui.fileLabel.textContent = "Choose Music File...";
    ui.thumbLabel.textContent = "Choose Cover Art...";
    ui.inputMusicFile.value = null;
    ui.inputMusicThumb.value = null;
});

ui.cancelBtn.addEventListener('click', () => {
    ui.modal.classList.add('hidden');
});

ui.tabText.addEventListener('click', () => switchTab('text'));
ui.tabMusic.addEventListener('click', () => switchTab('music'));

function switchTab(tab) {
    activeTab = tab;
    if (tab === 'text') {
        ui.tabText.classList.add('active');
        ui.tabMusic.classList.remove('active');
        ui.sectText.classList.remove('hidden');
        ui.sectMusic.classList.add('hidden');
    } else {
        ui.tabMusic.classList.add('active');
        ui.tabText.classList.remove('active');
        ui.sectMusic.classList.remove('hidden');
        ui.sectText.classList.add('hidden');
    }
}

ui.inputMusicFile.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        const file = e.target.files[0];
        ui.fileLabel.textContent = file.name;
        
        // Auto-fill Title
        if (!ui.inputMusicTitle.value) {
            ui.inputMusicTitle.value = file.name.replace(/\.[^/.]+$/, ""); 
        }

        // Attempt metadata extraction
        if (window.jsmediatags) {
            window.jsmediatags.read(file, {
                onSuccess: function(tag) {
                    const tags = tag.tags;
                    
                    // Title from tags?
                    if (tags.title) {
                        ui.inputMusicTitle.value = tags.title;
                    }

                    // Picture
                    const picture = tags.picture;
                    if (picture) {
                        let base64String = "";
                        for (let i = 0; i < picture.data.length; i++) {
                            base64String += String.fromCharCode(picture.data[i]);
                        }
                        const base64 = "data:" + picture.format + ";base64," + window.btoa(base64String);
                        
                        // Set as current thumb preview/data
                        ui.inputMusicThumb.dataset.autoThumb = base64;
                        ui.thumbLabel.textContent = "Cover Art Extracted!";
                        ui.thumbLabel.style.borderColor = "#c4b5fd";
                        ui.thumbLabel.style.color = "#fff";
                    } else {
                        ui.inputMusicThumb.dataset.autoThumb = "";
                        ui.thumbLabel.textContent = "No Embedded Cover (Click to Upload)";
                    }
                },
                onError: function(error) {
                    console.log("Metadata error:", error);
                    ui.inputMusicThumb.dataset.autoThumb = "";
                    ui.thumbLabel.textContent = "Metadata Error (Click to Upload)";
                }
            });
        }
    }
});

ui.inputMusicThumb.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        ui.thumbLabel.textContent = e.target.files[0].name;
        // Clear auto thumb if manual selected
        ui.inputMusicThumb.dataset.autoThumb = "";
    }
});

ui.saveBtn.addEventListener('click', async () => {
    if (activeTab === 'text') {
        const text = ui.inputText.value.trim();
        if (text) {
            addNote({ type: 'text', text: text });
            ui.modal.classList.add('hidden');
        }
    } else {
        const file = ui.inputMusicFile.files[0];
        const manualThumb = ui.inputMusicThumb.files[0];
        const autoThumb = ui.inputMusicThumb.dataset.autoThumb;
        const title = ui.inputMusicTitle.value.trim() || "Unknown Track";
        
        if (file) {
            let thumbSrc = ""; 
            if (manualThumb) {
                thumbSrc = await readFileAsDataURL(manualThumb);
            } else if (autoThumb) {
                thumbSrc = autoThumb;
            }

            // Read Audio File
            const audioBuffer = await readFileAsArrayBuffer(file);
            const blob = new Blob([audioBuffer], { type: file.type });
            const src = URL.createObjectURL(blob); // Immediate playback

            // Backend Save (Optional/Parallel)
            if (window.pywebview && window.pywebview.api) {
                // We typically send base64 to python, but for IDB we keep ArrayBuffer
                // Let's not block the UI for backend save
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = function() {
                    const b64 = reader.result.split(',')[1];
                    window.pywebview.api.save_music(file.name, b64).catch(e => console.log(e));
                };
            }
            
            addNote({ 
                type: 'music', 
                text: title, 
                src: src, // Session URL
                audioBuffer: audioBuffer, // Persistent Data
                audioType: file.type,
                thumb: thumbSrc 
            });
            ui.modal.classList.add('hidden');
        } else {
            alert("Please select a music file!");
        }
    }
});

// Helpers for File Reading
function readFileAsArrayBuffer(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsArrayBuffer(file);
    });
}

function readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function addNote(data) {
    const isMusic = data.type === 'music';
    const n = {
        id: Date.now().toString(),
        type: data.type || 'text',
        text: data.text,
        src: data.src, // Blob URL (temp) or Path
        audioBuffer: data.audioBuffer || null, // The actual file data
        audioType: data.audioType || null,
        thumb: data.thumb, 
        thumbImg: null,
        timestamp: new Date().toISOString(),
        x: -camera.x/camera.zoom + (window.innerWidth/2)/camera.zoom - BASE_WIDTH/2 + (Math.random()-0.5)*50,
        y: -camera.y/camera.zoom + (window.innerHeight/2)/camera.zoom - BASE_HEIGHT/2 + (Math.random()-0.5)*50,
        w: BASE_WIDTH,
        h: isMusic ? MUSIC_CARD_HEIGHT : BASE_HEIGHT,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        rotation: (Math.random() - 0.5) * 6,
        expanded: false,
        isPlaying: false,
        anim: { scale: 1.0, lift: 0, blur: 15, offset: 8 }
    };
    
    if (n.thumb) {
        const img = new Image();
        img.src = n.thumb;
        n.thumbImg = img;
    }

    notes.push(n);
    saveData();
}

// UI State (append new elements)
ui.deleteModal = document.getElementById('delete-modal');
ui.delConfirmBtn = document.getElementById('del-confirm-btn');
ui.delCancelBtn = document.getElementById('del-cancel-btn');

let noteToDeleteIndex = -1;

function requestDeleteNote(index) {
    noteToDeleteIndex = index;
    ui.deleteModal.classList.remove('hidden');
}

ui.delCancelBtn.addEventListener('click', () => {
    ui.deleteModal.classList.add('hidden');
    noteToDeleteIndex = -1;
});

ui.delConfirmBtn.addEventListener('click', () => {
    if (noteToDeleteIndex !== -1) {
        const n = notes[noteToDeleteIndex];
        if (n.isPlaying) stopMusic();
        notes.splice(noteToDeleteIndex, 1);
        saveData();
        ui.deleteModal.classList.add('hidden');
        noteToDeleteIndex = -1;
    }
});

function deleteNote(index) {
    // Deprecated direct call, now routing through request
    requestDeleteNote(index);
}

// --- Music Logic ---
function toggleMusic(note) {
    if (currentPlayingNoteId === note.id) {
        if (currentAudio.paused) {
            currentAudio.play();
            note.isPlaying = true;
        } else {
            currentAudio.pause();
            note.isPlaying = false;
        }
    } else {
        stopMusic();
        
        currentPlayingNoteId = note.id;
        note.isPlaying = true;
        
        currentAudio = new Audio(note.src);
        currentAudio.loop = true; 
        currentAudio.play().catch(e => {
            console.error("Playback failed", e);
            note.isPlaying = false;
            currentPlayingNoteId = null;
            alert("Could not play audio.");
        });
        
        currentAudio.onended = () => {
            note.isPlaying = false;
            currentPlayingNoteId = null;
        };
    }
}

function stopMusic() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    if (currentPlayingNoteId) {
        const n = notes.find(x => x.id === currentPlayingNoteId);
        if (n) n.isPlaying = false;
        currentPlayingNoteId = null;
    }
}

// --- IndexedDB Helpers ---
const dbName = "StickyNotesDB";
const storeName = "notes";

function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(dbName, 1);
        request.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains(storeName)) {
                db.createObjectStore(storeName, { keyPath: "id" });
            }
        };
        request.onsuccess = (e) => resolve(e.target.result);
        request.onerror = (e) => reject(e.target.error);
    });
}

async function saveToIDB(data) {
    try {
        const db = await openDB();
        const tx = db.transaction(storeName, "readwrite");
        const store = tx.objectStore(storeName);
        
        // Clear and rewrite to ensure sync
        await new Promise((resolve, reject) => {
             const clearReq = store.clear();
             clearReq.onsuccess = resolve;
             clearReq.onerror = reject;
        });
        
        const promises = data.map(item => {
            return new Promise((resolve, reject) => {
                const req = store.put(item);
                req.onsuccess = resolve;
                req.onerror = reject;
            });
        });
        await Promise.all(promises);
    } catch (e) {
        console.error("IDB Save Error:", e);
    }
}

async function loadFromIDB() {
    try {
        const db = await openDB();
        const tx = db.transaction(storeName, "readonly");
        const store = tx.objectStore(storeName);
        return await new Promise((resolve, reject) => {
            const req = store.getAll();
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
        });
    } catch (e) {
        console.error("IDB Load Error:", e);
        return [];
    }
}

// --- Data Fetching ---
async function fetchData() {
    if (isDraggingNote || !ui.modal.classList.contains('hidden')) return;

    try {
        let rawData = [];
        
        // 1. Try IndexedDB (Persistent Local State)
        const idbData = await loadFromIDB();
        
        if (idbData && idbData.length > 0) {
            rawData = idbData;
        } else {
            // 2. Fallback to Backend/JSON if IDB empty
            if (window.pywebview && window.pywebview.api) {
                rawData = await window.pywebview.api.get_data();
            } else {
                const res = await fetch('user_inputs.json?t=' + Date.now());
                if (res.ok) rawData = await res.json();
            }
        }

        const jsonStr = JSON.stringify(rawData);
        if (jsonStr !== previousDataStr) {
            processNotes(rawData);
            previousDataStr = jsonStr;
        }
    } catch (e) { console.error("Fetch Error:", e); }
}

async function saveData() {
    const dataToSave = notes.map(n => ({
        id: n.id,
        type: n.type,
        text: n.text,
        src: n.src,
        audioBuffer: n.audioBuffer, // Save the big buffer to IDB
        audioType: n.audioType,
        thumb: n.thumb,
        timestamp: n.timestamp,
        x: n.x, y: n.y,
        rotation: n.rotation,
        color: n.color
    }));
    
    // Save to IndexedDB (Primary)
    await saveToIDB(dataToSave);
    
    // For backend, we might want to STRIP audioBuffer to save bandwidth if it's huge?
    // But user asked for IDB persistence mostly.
    
    // Sync to Backend (Secondary)
    if (window.pywebview && window.pywebview.api) {
        // Strip buffer for JSON file to avoid massive file size
        const liteData = dataToSave.map(n => {
            const { audioBuffer, ...rest } = n; 
            return rest;
        });
        window.pywebview.api.save_data(liteData).catch(e => console.error("Backend Save Error:", e));
    }
}

function processNotes(data) {
    notes = data.map((item, index) => {
        const match = notes.find(n => n.id === item.id);
        
        let startX = item.x || (80 + (index%4)*(BASE_WIDTH+PADDING));
        let startY = item.y || (80 + Math.floor(index/4)*(BASE_HEIGHT+PADDING));
        
        const isMusic = item.type === 'music';
        
        // Regenerate Blob URL if we have persistent buffer
        let activeSrc = item.src;
        if (item.audioBuffer && item.audioType) {
            const blob = new Blob([item.audioBuffer], { type: item.audioType });
            activeSrc = URL.createObjectURL(blob);
        }

        const n = {
            id: item.id || index.toString(),
            type: item.type || 'text',
            text: item.text || item.question || "",
            src: activeSrc,
            audioBuffer: item.audioBuffer, // Keep it
            audioType: item.audioType,
            thumb: item.thumb || null,
            thumbImg: match ? match.thumbImg : null,
            x: startX,
            y: startY,
            w: (match && match.expanded) ? EXPANDED_WIDTH : BASE_WIDTH,
            h: (match && match.expanded) ? match.h : (isMusic ? MUSIC_CARD_HEIGHT : BASE_HEIGHT),
            color: item.color || COLORS[index % COLORS.length],
            timestamp: item.timestamp,
            rotation: item.rotation || (Math.random()-0.5)*8,
            expanded: match ? match.expanded : false,
            isPlaying: match ? match.isPlaying : false, 
            dateTime: item.timestamp ? new Date(item.timestamp).toLocaleString([], {
                month: 'short', day: 'numeric', hour: '2-digit', minute:'2-digit'
            }) : "",
            anim: match ? match.anim : { scale: 1.0, lift: 0, blur: 15, offset: 8 }
        };

        if (n.thumb && !n.thumbImg) {
            const img = new Image();
            img.src = n.thumb;
            n.thumbImg = img;
        }
        
        return n;
    });
}

function wrapText(text, maxWidth) {
    if (!text) return [""];
    const words = text.split(' ');
    let lines = [];
    let curLine = words[0];

    for (let i = 1; i < words.length; i++) {
        const width = ctx.measureText(curLine + " " + words[i]).width;
        if (width < maxWidth) {
            curLine += " " + words[i];
        } else {
            lines.push(curLine);
            curLine = words[i];
        }
    }
    lines.push(curLine);
    return lines;
}

// --- Rendering ---
function draw() {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    // Dark bg
    ctx.fillStyle = "#1e1e24"; 
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Grid
    ctx.fillStyle = "#2b2b36";
    const spacing = 40 * camera.zoom;
    const ox = camera.x % spacing;
    const oy = camera.y % spacing;
    
    for (let x = ox; x < canvas.width; x += spacing) {
        for (let y = oy; y < canvas.height; y += spacing) {
            ctx.beginPath();
            ctx.arc(x, y, 2 * camera.zoom, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    ctx.setTransform(camera.zoom, 0, 0, camera.zoom, camera.x, camera.y);

    // Threads
    if (notes.length > 1) {
        ctx.strokeStyle = "rgba(255, 255, 255, 0.15)"; 
        ctx.lineWidth = 2;
        ctx.setLineDash([]);
        ctx.beginPath();
        for (let i = 0; i < notes.length - 1; i++) {
            const curr = notes[i];
            const next = notes[i+1];
            ctx.moveTo(curr.x + curr.w/2, curr.y + 10);
            const midX = (curr.x + next.x)/2 + (curr.w+next.w)/4;
            const midY = (curr.y + next.y)/2 + 50; 
            ctx.quadraticCurveTo(midX, midY, next.x + next.w/2, next.y + 10);
        }
        ctx.stroke();
    }

    // Notes
    notes.forEach(note => {
        // Anim Logic
        const wx = (lastMouse.x - camera.x) / camera.zoom;
        const wy = (lastMouse.y - camera.y) / camera.zoom;
        
        let targetScale = 1.0;
        let isHovered = false;

        if (wx > note.x && wx < note.x + note.w &&
            wy > note.y && wy < note.y + note.h && !isDraggingNote) {
            targetScale = 1.02;
            isHovered = true;
        }
        if (draggedNote === note) targetScale = 1.05;
        
        const f = 0.2;
        note.anim.scale += (targetScale - note.anim.scale) * f;

        ctx.save();
        const cx = note.x + note.w / 2;
        const cy = note.y + note.h / 2;
        ctx.translate(cx, cy);
        ctx.rotate(note.rotation * Math.PI / 180);
        ctx.scale(note.anim.scale, note.anim.scale);

        // Shadow
        ctx.shadowColor = "rgba(0,0,0,0.5)";
        ctx.shadowBlur = 20;
        ctx.shadowOffsetY = 10;

        // Render based on Type
        if (note.type === 'music') {
            drawMusicCard(ctx, note, isHovered);
        } else {
            drawTextNote(ctx, note, isHovered);
        }

        ctx.restore();
    });
}

function drawTextNote(ctx, note, isHovered) {
    // Body
    ctx.fillStyle = note.color;
    ctx.fillRect(-note.w/2, -note.h/2, note.w, note.h);
    
    // Tape
    ctx.shadowColor = "transparent";
    ctx.fillStyle = "rgba(255,255,255,0.3)";
    ctx.fillRect(-15, -note.h/2 - 5, 30, 20); 
    ctx.fillStyle = "#e74c3c";
    ctx.beginPath(); ctx.arc(0, -note.h/2 + 5, 4, 0, Math.PI*2); ctx.fill();
    
    // Delete Button
    if (isHovered && !draggedNote) {
        drawDeleteBtn(ctx, note);
    }

    // Text Content
    ctx.fillStyle = "#1e293b";
    ctx.font = "14px 'Kalam', cursive";
    ctx.textAlign = "right";
    if (note.dateTime) {
        ctx.fillStyle = "#4b5563";
        ctx.fillText(note.dateTime, note.w/2 - 10, note.h/2 - 15);
    }

    ctx.font = "24px 'Kalam', cursive";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "#1e293b";
    
    let displayLines = wrapText(note.text, note.w - 40);
    if (!note.expanded && displayLines.length > 4) {
            displayLines = displayLines.slice(0, 3);
            displayLines.push("...");
    }
    
    const lh = 30;
    const totalH = displayLines.length * lh;
    let startY = -totalH / 2 - 10;

    displayLines.forEach((line, i) => {
        ctx.fillText(line, 0, startY + i * lh);
    });
}

function drawMusicCard(ctx, note, isHovered) {
    const w = note.w;
    const h = note.h;
    
    // Glassmorphism / Frosted Card Look
    // Clip rounded rect
    ctx.beginPath();
    ctx.roundRect(-w/2, -h/2, w, h, 16);
    ctx.clip();

    // Background
    ctx.fillStyle = "#2c2c35"; 
    ctx.fillRect(-w/2, -h/2, w, h);

    // Cover Art (Top Area)
    const coverH = h * 0.65;
    if (note.thumbImg && note.thumbImg.complete) {
        try {
            // Draw Image cover style
            // We want to fill the top area
            const imgAspect = note.thumbImg.width / note.thumbImg.height;
            const areaAspect = w / coverH;
            
            let dw, dh, dx, dy;
            if (imgAspect > areaAspect) {
                dh = coverH;
                dw = dh * imgAspect;
                dx = -w/2 + (w - dw)/2;
                dy = -h/2;
            } else {
                dw = w;
                dh = dw / imgAspect;
                dx = -w/2;
                dy = -h/2 + (coverH - dh)/2;
            }
            
            ctx.save();
            ctx.beginPath(); ctx.rect(-w/2, -h/2, w, coverH); ctx.clip();
            ctx.drawImage(note.thumbImg, dx, dy, dw, dh);
            ctx.restore();
            
        } catch(e) { }
    } else {
        // Fallback Gradient
        const grad = ctx.createLinearGradient(-w/2, -h/2, w/2, coverH - h/2);
        grad.addColorStop(0, note.color);
        grad.addColorStop(1, "#333");
        ctx.fillStyle = grad;
        ctx.fillRect(-w/2, -h/2, w, coverH);
        
        // Music Note Icon
        ctx.fillStyle = "rgba(255,255,255,0.2)";
        ctx.font = "60px Arial";
        ctx.fillText("♫", 0, -h/2 + coverH/2);
    }

    // Controls Area (Bottom)
    ctx.fillStyle = "rgba(30, 30, 35, 0.9)";
    ctx.fillRect(-w/2, -h/2 + coverH, w, h - coverH);

    // Play/Pause Button (Bottom Right)
    const btnX = w/2 - 35;
    const btnY = h/2 - 35;
    
    ctx.beginPath();
    ctx.arc(btnX, btnY, 25, 0, Math.PI*2);
    ctx.fillStyle = note.isPlaying ? "#f43f5e" : "#e2e8f0"; // Pink if playing, White if stopped
    ctx.fill();
    
    // Icon
    ctx.fillStyle = note.isPlaying ? "#fff" : "#1e293b";
    if (note.isPlaying) {
        ctx.fillRect(btnX - 6, btnY - 8, 4, 16);
        ctx.fillRect(btnX + 2, btnY - 8, 4, 16);
    } else {
        ctx.beginPath();
        ctx.moveTo(btnX - 5, btnY - 8);
        ctx.lineTo(btnX + 8, btnY);
        ctx.lineTo(btnX - 5, btnY + 8);
        ctx.fill();
    }

    // Title & Artist
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    
    // Title
    ctx.font = "bold 18px 'Kalam', cursive";
    ctx.fillStyle = "#fff";
    const title = note.text.length > 15 ? note.text.substring(0, 14) + "..." : note.text;
    ctx.fillText(title, -w/2 + 20, -h/2 + coverH + 20);
    
    // Subtitle / Status
    ctx.font = "italic 14px 'Kalam', cursive";
    ctx.fillStyle = "#94a3b8";
    ctx.fillText(note.isPlaying ? "Now Playing..." : "Music Track", -w/2 + 20, -h/2 + coverH + 45);

    // Delete Button (Standard position: Top Right of CARD)
    // Redo logic: Draw it relative to Card center
    if (isHovered && !draggedNote) {
        drawDeleteBtn(ctx, note);
    }
}

function drawDeleteBtn(ctx, note) {
    ctx.fillStyle = "#ff4757";
    const dx = note.w/2 - 15;
    const dy = -note.h/2 + 15;
    ctx.beginPath(); ctx.arc(dx, dy, 12, 0, Math.PI*2); ctx.fill();
    ctx.fillStyle = "white";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "bold 14px Arial";
    ctx.fillText("✕", dx, dy + 1);
}

function animate() {
    draw();
    requestAnimationFrame(animate);
}

// Start
fetchData();
setInterval(fetchData, 2000);
animate();
