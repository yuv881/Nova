// --- THREE.JS MINIMAL SETUP ---
let scene, camera, renderer, sphere;
let isSpeaking = false;
let isListening = false;

// DOM Elements
const micButton = document.getElementById('mic-button');
const statusText = document.getElementById('status-text');
const chatArea = document.getElementById('chat-area');

function init3D() {
    const container = document.getElementById('canvas-container');

    if (!container) {
        console.error("Canvas container not found!");
        return;
    }

    // Scene
    scene = new THREE.Scene();
    // Minimal fog for depth
    scene.fog = new THREE.FogExp2(0x050505, 0.05);

    // Camera
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 4;

    // Renderer
    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // Minimal Sphere
    // Using a high detail geometry for smooth look
    const geometry = new THREE.IcosahedronGeometry(1.2, 10); // High detail

    // Shader-like material using standard material with specific settings
    const material = new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        metalness: 0.1,
        roughness: 0.2,
        transmission: 0.0, // Glass-like
        wireframe: true,   // Wireframe looks techy but minimal
        wireframeLinewidth: 1.5,
        emissive: 0x000000,
        side: THREE.DoubleSide
    });

    sphere = new THREE.Mesh(geometry, material);
    scene.add(sphere);

    // Lights
    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);

    const light1 = new THREE.PointLight(0xffffff, 1);
    light1.position.set(10, 10, 10);
    scene.add(light1);

    const light2 = new THREE.PointLight(0x4444ff, 1);
    light2.position.set(-10, -10, 5);
    scene.add(light2);

    animate();
}

// Time variable for wave animation
let t = 0;

function animate() {
    requestAnimationFrame(animate);
    t += 0.01;

    if (sphere) {
        // Gentle Rotation
        sphere.rotation.y += 0.002;
        sphere.rotation.x = Math.sin(t * 0.5) * 0.1;

        // Dynamic State Animation
        if (isListening) {
            // Pulse and turn slightly active
            const scale = 1.2 + Math.sin(t * 10) * 0.05;
            sphere.scale.setScalar(scale);
            sphere.material.color.setHex(0xffffff); // Bright White
            sphere.material.wireframeLinewidth = 2;
            sphere.rotation.y += 0.02;
        } else if (isSpeaking) {
            // Wave motion
            const scale = 1.0 + Math.sin(t * 20) * 0.1;
            sphere.scale.setScalar(scale);
            sphere.material.color.setHex(0xaaddff); // Soft Blue
            sphere.rotation.z += 0.01;
        } else {
            // Idle breathing
            const scale = 1.0 + Math.sin(t * 2) * 0.02;
            sphere.scale.setScalar(scale);
            sphere.material.color.setHex(0x555555); // Dim Grey
            sphere.material.wireframeLinewidth = 1;
        }
    }

    renderer.render(scene, camera);
}

// Handle Window Resize
window.addEventListener('resize', () => {
    if (camera && renderer) {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }
});

// Initialize 3D Scene
// Wait for DOM to be ready just in case
document.addEventListener('DOMContentLoaded', init3D);


// --- VOICE LOGIC ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
    alert("Your browser does not support Speech Recognition. Please use Chrome or Edge.");
    if (statusText) statusText.textContent = "NOT SUPPORTED";
}

const recognition = new SpeechRecognition();
recognition.lang = 'en-US';
recognition.interimResults = false;
recognition.maxAlternatives = 1;

if (micButton) {
    micButton.addEventListener('click', () => {
        if (isListening) {
            recognition.stop();
        } else {
            try {
                recognition.start();
            } catch (e) {
                console.error("Recognition start error:", e);
            }
        }
    });
}

recognition.onstart = () => {
    isListening = true;
    if (micButton) micButton.classList.add('active');
    if (statusText) statusText.textContent = "LISTENING...";
};

recognition.onend = () => {
    isListening = false;
    if (micButton) micButton.classList.remove('active');
};

recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    if (statusText) statusText.textContent = "PROCESSING...";
    addMessage(transcript, 'user');
    sendToBackend(transcript);
};

recognition.onerror = (event) => {
    console.error("Speech Recognition Error:", event.error);
    if (statusText) statusText.textContent = "ERROR: " + event.error;
    isListening = false;
    if (micButton) micButton.classList.remove('active');
};

function addMessage(text, sender) {
    if (!chatArea) return;
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    messageDiv.textContent = text;
    chatArea.appendChild(messageDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
}

async function sendToBackend(message) {
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        const aiResponse = data.response;

        addMessage(aiResponse, 'ai');
        speak(aiResponse);

    } catch (error) {
        console.error('Error:', error);
        if (statusText) statusText.textContent = "CONNECTION ERROR";
        addMessage("Server unreachable.", 'ai');
    }
}

function speak(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);

        let voices = window.speechSynthesis.getVoices();
        const setVoice = () => {
            voices = window.speechSynthesis.getVoices();
            const preferredVoice = voices.find(voice =>
            (voice.name.includes('Google US English') ||
                voice.name.includes('Microsoft Zira') ||
                voice.name.includes('Samantha'))
            );
            if (preferredVoice) utterance.voice = preferredVoice;
        };

        if (voices.length === 0) {
            window.speechSynthesis.onvoiceschanged = setVoice;
        } else {
            setVoice();
        }

        utterance.onstart = () => {
            isSpeaking = true;
            if (statusText) statusText.textContent = "VOCALIZING...";
        };

        utterance.onend = () => {
            isSpeaking = false;
            if (statusText) statusText.textContent = "SYSTEM ONLINE";
        };

        utterance.onerror = (e) => {
            isSpeaking = false;
            if (statusText) statusText.textContent = "SYSTEM ONLINE";
        };

        window.speechSynthesis.speak(utterance);
    }
}
