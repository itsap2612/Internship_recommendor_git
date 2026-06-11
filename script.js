function openProfileModal() {
    document.getElementById('profileModal').classList.add('active');
}

function closeProfileModal() {
    document.getElementById('profileModal').classList.remove('active');
}

// MODIFIED to accept optional arguments for the chatbot
async function performSearch(query, loc) {
    // If query/loc are not passed, get them from the main search inputs
    const input = query || document.getElementById("searchInput").value.trim();
    const location = loc || document.getElementById("locationInput").value.trim();
    
    if (!input) return alert("Please enter your skills or interests.");

    document.getElementById("loadingSpinner").classList.add("active");
    // Clear previous results when a new search starts
    const grid = document.getElementById("internshipGrid");
    grid.innerHTML = "";
    document.getElementById("recommendationsSection").classList.add("active");


    try {
        const response = await fetch("http://127.0.0.1:5000/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                resume: input,
                location: location,
                top_k: 5 
            })
        });

        const data = await response.json();
        grid.innerHTML = ""; // Clear again to be safe

        if (data.results && data.results.length > 0) {
            data.results.forEach(job => {
                const card = document.createElement("div");
                card.className = "internship-card";
                card.innerHTML = `
                    <div class="match-badge">${Math.round(job.score * 100)}% Match</div>
                    <div class="company-header">
                        <div class="company-logo">${job.title.charAt(0)}</div>
                        <div class="company-info">
                            <h3>${job.title}</h3>
                            <p>${job.company} - ${job.location}</p>
                        </div>
                    </div>
                    <div class="internship-details">${job.description}</div>
                    <div class="skill-tags">${job.skills_required.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}</div>
                    <a href="${job.link}" target="_blank"><button class="apply-btn">Apply Now</button></a>
                `;
                grid.appendChild(card);
            });
            document.getElementById("recommendationsSection").classList.add("active");
        } else {
            grid.innerHTML = "<p>No internships found for your skills.</p>";
        }
    } catch (err) {
        console.error(err);
        alert("Error fetching recommendations from the server.");
    } finally {
        document.getElementById("loadingSpinner").classList.remove("active");
    }
}


function toggleFilter(el, filter) {
    el.classList.toggle("active");
    const input = document.getElementById("searchInput");
    const filters = Array.from(document.querySelectorAll(".filter-chip.active")).map(f => f.textContent);
    input.value = filters.join(" ");
    performSearch();
}

async function submitProfile() {
    const name = document.getElementById("profileName").value;
    const skills = document.getElementById("profileSkills").value;
    const interests = document.getElementById("profileInterests").value;

    if (!name || !skills) {
        return alert("Name and Skills are required.");
    }

    try {
        const response = await fetch("http://127.0.0.1:5000/create-profile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, skills, interests })
        });
        const result = await response.json();
        if (response.ok) {
            alert("Profile created successfully!");
            closeProfileModal();
        } else {
            alert("Error creating profile: " + result.error);
        }
    } catch (err) {
        console.error(err);
        alert("Error connecting to server to create profile.");
    }
}

// --- Voice Search Implementation ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    const voiceSearchBtn = document.getElementById("voiceSearchBtn");
    const searchInput = document.getElementById("searchInput");
    const locationInput = document.getElementById("locationInput");

    voiceSearchBtn.addEventListener("click", () => {
        recognition.start();
        voiceSearchBtn.textContent = "Listening...";
        voiceSearchBtn.disabled = true;
    });

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        let query = transcript;
        let location = "";
        const inPattern = / in /i;
        if (inPattern.test(transcript)) {
            const parts = transcript.split(inPattern);
            query = parts[0];
            location = parts[1];
        }
        searchInput.value = query.trim();
        locationInput.value = location.trim();
        performSearch();
    };

    recognition.onerror = function(event) {
        console.error("Speech recognition error:", event.error);
        alert(`Error during voice recognition: ${event.error}`);
    };
    
    recognition.onend = function() {
        voiceSearchBtn.textContent = "🎙️";
        voiceSearchBtn.disabled = false;
    };

} else {
    console.warn("Speech Recognition API not supported in this browser.");
    const voiceSearchBtn = document.getElementById("voiceSearchBtn");
    if (voiceSearchBtn) {
        voiceSearchBtn.style.display = 'none';
    }
}


// --- START: Chatbot Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const chatToggle = document.getElementById('chatToggle');
    const chatWidget = document.getElementById('chatWidget');
    const closeChat = document.getElementById('closeChat');
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');

    // Toggle chat widget visibility
    chatToggle.addEventListener('click', () => {
        chatWidget.classList.toggle('active');
    });

    closeChat.addEventListener('click', () => {
        chatWidget.classList.remove('active');
    });

    // Handle message submission
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const userInput = chatInput.value.trim();
        if (!userInput) return;

        // Add user message to chat and clear input
        addUserMessage(userInput);
        chatInput.value = '';

        // Trigger the search using the chatbot's input
        addBotMessage("Searching for internships for you...");
        performSearch(userInput, ''); // Use the modified function
    });

    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message';
        messageElement.innerHTML = `<p>${message}</p>`;
        chatMessages.appendChild(messageElement);
        scrollToBottom();
    }



    function addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message';
        messageElement.innerHTML = `<p>${message}</p>`;
        chatMessages.appendChild(messageElement);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
// --- END: Chatbot Logic ---