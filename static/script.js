document.addEventListener("DOMContentLoaded", () => {
    // --- Daily Tip Logic ---
    const detailedTips = [
        { title: "Stay Hydrated", icon: "fa-glass-water", text: "Drinking enough water is critical for brain health. Even mild dehydration can impair short-term memory, focus, and decision-making." },
        { title: "Prioritize Sleep", icon: "fa-bed", text: "Quality sleep allows the brain to clear out toxins that accumulate during waking hours. Aim for 7-9 hours of uninterrupted sleep every night to reduce the risk of cognitive decline." },
        { title: "Reduce Screen Stress", icon: "fa-display", text: "Staring at screens for long periods can cause eye strain and mental fatigue. Practice the 20-20-20 rule: every 20 minutes, look at something 20 feet away for 20 seconds." },
        { title: "Engage in Mental Exercises", icon: "fa-puzzle-piece", text: "Keep your brain active and challenged. Activities like reading, solving puzzles, learning a new language, or playing an instrument can build cognitive reserves." },
        { title: "Maintain a Healthy Diet", icon: "fa-apple-whole", text: "A diet rich in antioxidants, healthy fats (like Omega-3s from fish), and whole foods can protect brain cells and reduce inflammation. Mediterranean diets are highly recommended." },
        { title: "Regular Exercise", icon: "fa-person-running", text: "Physical activity increases blood flow to the brain, promoting the growth of new blood vessels and brain cells. Aim for at least 30 minutes of moderate exercise most days." },
        { title: "Avoid Smoking", icon: "fa-ban-smoking", text: "Smoking harms blood vessels and can reduce the amount of oxygen reaching your brain. Quitting smoking significantly lowers your risk of neurodegenerative diseases." },
        { title: "Routine Checkups", icon: "fa-stethoscope", text: "Routine medical checkups can help catch early markers for vascular disease or neurological issues before they progress. Prevention is always the best medicine." }
    ];

    const brainCloudContainer = document.getElementById("brain-cloud-container");
    if(brainCloudContainer) {
        // Select 4 unique random tips
        const shuffled = detailedTips.sort(() => 0.5 - Math.random());
        const selectedTips = shuffled.slice(0, 4);
        
        for (let i = 0; i < 4; i++) {
            const tip = selectedTips[i];
            const titleEl = document.getElementById(`cloud-title-${i+1}`);
            const textEl = document.getElementById(`cloud-text-${i+1}`);
            if (titleEl && textEl) {
                titleEl.innerHTML = `<i class="fa-solid ${tip.icon}"></i> ${tip.title}`;
                textEl.innerText = tip.text;
            }
        }
    }

    // --- Core Core App Logic ---
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const previewContainer = document.getElementById('preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removeBtn = document.getElementById('remove-btn');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    // Sections
    const uploadSection = document.getElementById('upload-section');
    const scanningSection = document.getElementById('scanning-section');
    const resultSection = document.getElementById('result-section');
    const resultCard = document.getElementById('result-card');
    const resultIcon = document.getElementById('result-icon');
    const resultText = document.getElementById('result-text');
    const resultTips = document.getElementById('result-tips');
    const retryBtn = document.getElementById('retry-btn');
    
    // Drag and Drop Logic
    dropZone.addEventListener('click', () => {
        if (!fileInput.files.length) fileInput.click();
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFile(fileInput.files[0]);
        }
    });

    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            handleFile(this.files[0]);
        }
    });

    function handleFile(file) {
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                dropZone.style.display = 'none';
                previewContainer.style.display = 'block';
                analyzeBtn.disabled = false;
            };
            reader.readAsDataURL(file);
        } else {
            alert("Please upload a valid image file.");
            resetUI();
        }
    }

    removeBtn.addEventListener('click', resetUI);
    retryBtn.addEventListener('click', resetUI);

    function resetUI() {
        fileInput.value = '';
        imagePreview.src = '#';
        previewContainer.style.display = 'none';
        document.getElementById('scanning-overlay').style.display = 'none';
        document.getElementById('neural-grid').style.display = 'none';
        dropZone.style.display = 'flex';
        analyzeBtn.disabled = true;
        
        scanningSection.style.display = 'none';
        resultSection.style.display = 'none';
        uploadSection.style.display = 'block';
        
        resultCard.className = 'result-card';
        document.getElementById('upload-section').scrollIntoView({behavior: 'smooth'});
    }

    // Audio Context for subtle ding
    function playDing() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            const audioCtx = new AudioContext();
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(800, audioCtx.currentTime); // high ping
            gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.3, audioCtx.currentTime + 0.05);
            gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.5);
            
            oscillator.start(audioCtx.currentTime);
            oscillator.stop(audioCtx.currentTime + 0.6);
        } catch(e) {
            console.log("Audio not supported");
        }
    }

    // Form Submit
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        // Show scanning animation
        document.getElementById('scanning-overlay').style.display = 'block';
        document.getElementById('neural-grid').style.display = 'block';
        uploadSection.style.display = 'none';
        scanningSection.style.display = 'block';
        document.getElementById('scanning-section').scrollIntoView({behavior: 'smooth'});

        // Fake standard delay to show off animation (2-3 sec)
        const delay = new Promise(resolve => setTimeout(resolve, 2500));
        
        try {
            const fetchResult = fetch('/predict', {
                method: 'POST',
                body: formData
            }).then(r => r.json());
            
            const [data] = await Promise.all([fetchResult, delay]);
            
            showResult(data);
        } catch (err) {
            console.error("Prediction error:", err);
            alert("An error occurred during analysis. Please try again.");
            resetUI();
        }
    });

    function showResult(data) {
        scanningSection.style.display = 'none';
        resultSection.style.display = 'block';
        document.getElementById('result-section').scrollIntoView({behavior: 'smooth'});
        
        playDing();
        
        resultText.innerText = data.prediction;
        
        // Dynamic UI changes based on result
        if (data.prediction.toLowerCase().includes("no tumor") || data.prediction.toLowerCase().includes("negative")) {
            // Negative (Success)
            resultCard.className = 'result-card success-card';
            resultIcon.className = 'fa-solid fa-shield-check result-icon';
            resultTips.innerHTML = `
                <ul>
                    <li><i class="fa-solid fa-check"></i> Maintain a healthy lifestyle</li>
                    <li><i class="fa-solid fa-check"></i> Schedule regular medical checkups</li>
                </ul>
            `;
        } else {
            // Positive (Warning)
            resultCard.className = 'result-card danger-card';
            resultIcon.className = 'fa-solid fa-triangle-exclamation result-icon';
            resultText.innerText = "Brain tumor detected. Consult a doctor immediately.";
            resultTips.innerHTML = `
                <ul>
                    <li><i class="fa-solid fa-user-doctor"></i> Seek medical consultation immediately</li>
                    <li><i class="fa-solid fa-spa"></i> Avoid unnecessary stress</li>
                    <li><i class="fa-solid fa-bed"></i> Maintain proper sleep and hydration</li>
                </ul>
            `;
        }
    }

    // Chatbot Logic
    const chatbotBtn = document.getElementById("chatbot-btn");
    const chatWindow = document.getElementById("chat-window");
    const closeChatBtn = document.getElementById("close-chat-btn");
    const chatInput = document.getElementById("chat-input");
    const sendChatBtn = document.getElementById("send-chat-btn");
    const chatBody = document.getElementById("chat-body");

    if (chatbotBtn && chatWindow) {
        chatbotBtn.addEventListener("click", () => {
            chatWindow.style.display = "flex";
            chatbotBtn.style.display = "none";
        });

        closeChatBtn.addEventListener("click", () => {
            chatWindow.style.display = "none";
            chatbotBtn.style.display = "flex";
        });

        const sendMessage = async () => {
            const text = chatInput.value.trim();
            if (!text) return;

            const userBox = document.createElement("div");
            userBox.className = "message user-message";
            userBox.innerText = text;
            chatBody.appendChild(userBox);
            chatInput.value = "";
            chatBody.scrollTop = chatBody.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                
                const data = await response.json();
                
                const botBox = document.createElement("div");
                botBox.className = "message bot-message";
                botBox.innerText = data.reply;
                chatBody.appendChild(botBox);
                chatBody.scrollTop = chatBody.scrollHeight;
                
            } catch (err) {
                console.error("Chat error:", err);
            }
        };

        sendChatBtn.addEventListener("click", sendMessage);
        chatInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") sendMessage();
        });

        const suggestionBtns = document.querySelectorAll(".suggestion-btn");
        suggestionBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                chatInput.value = btn.getAttribute("data-query");
                sendMessage();
            });
        });
    }
});
