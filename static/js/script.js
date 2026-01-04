/* static/js/script.js - FINAL COMPLETE VERSION */

// --- GLOBAL VARIABLES FOR DASHBOARD ---
let currentStep = 1; 
let cardFile = null;
let qrFile = null;

document.addEventListener('DOMContentLoaded', () => {
    
    // =========================================================
    // 1. THEME TOGGLE LOGIC
    // =========================================================
    const toggleBtn = document.getElementById('theme-toggle');
    const icon = toggleBtn ? toggleBtn.querySelector('i') : null;
    const htmlElement = document.documentElement;
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    htmlElement.setAttribute('data-theme', savedTheme);
    if(icon) icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            htmlElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            if(icon) icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        });
    }

    // =========================================================
    // 2. AUTHENTICATION LOGIC (Login & Signup) - RESTORED
    // =========================================================
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const messageDiv = document.getElementById('message');

    function showAuthMessage(type, text) {
        if(messageDiv) {
            messageDiv.className = `message ${type}`;
            messageDiv.innerText = text;
            messageDiv.classList.remove('hidden');
            messageDiv.style.display = 'block';
        }
    }

    // --- LOGIN HANDLER ---
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault(); // STOP page reload
            const formData = new FormData(loginForm);
            const data = Object.fromEntries(formData.entries());
            
            // Checkbox handling
            const rememberBox = document.getElementById('remember');
            data.remember = rememberBox ? rememberBox.checked : false;

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                
                if (result.success) {
                    window.location.href = result.redirect_url;
                } else {
                    showAuthMessage('error', result.message);
                }
            } catch (error) {
                console.error("Login Error:", error);
                showAuthMessage('error', 'Server connection failed. Please try again.');
            }
        });
    }

    // --- SIGNUP HANDLER ---
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault(); // STOP page reload
            const formData = new FormData(signupForm);
            const data = Object.fromEntries(formData.entries());

            if (data.password !== data.confirm_password) {
                showAuthMessage('error', 'Passphrases do not match.');
                return;
            }

            try {
                const response = await fetch('/api/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                
                if (result.success) {
                    showAuthMessage('success', result.message);
                    setTimeout(() => window.location.href = result.redirect_url, 2000);
                } else {
                    showAuthMessage('error', result.message);
                }
            } catch (error) {
                console.error("Signup Error:", error);
                showAuthMessage('error', 'Server connection failed. Please try again.');
            }
        });
    }

    // =========================================================
    // 3. DASHBOARD UPLOAD LOGIC
    // =========================================================
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('cardInput');
    const previewImg = document.getElementById('image-preview');
    const placeholder = document.getElementById('upload-placeholder');
    const clearBtn = document.getElementById('clear-image-btn');

    if (dropZone && fileInput) {
        // Handle File Selection
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                // Determine which step we are on to save the correct file
                if (currentStep === 1) cardFile = file;
                else qrFile = file;

                const reader = new FileReader();
                reader.onload = (e) => {
                    previewImg.src = e.target.result;
                    previewImg.classList.remove('hidden');
                    if(placeholder) placeholder.classList.add('hidden');
                    if(clearBtn) clearBtn.classList.remove('hidden');
                };
                reader.readAsDataURL(file);
            }
        });

        // Handle Clear "X" Button
        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Stop click from bubbling to dropZone
                fileInput.value = ''; 
                previewImg.src = '';
                previewImg.classList.add('hidden');
                if(placeholder) placeholder.classList.remove('hidden');
                clearBtn.classList.add('hidden');
                
                if (currentStep === 1) cardFile = null;
                else qrFile = null;
            });
        }

        // Trigger file input when clicking zone
        dropZone.addEventListener('click', () => fileInput.click());
    }
});

// =========================================================
// 4. MAIN EXECUTION FLOW (Step 1 -> Step 2)
// =========================================================

async function handleExecution() {
    if (currentStep === 1) {
        await executeStep1();
    } else {
        await executeStep2();
    }
}

// --- STEP 1: VERIFY AADHAAR ---
async function executeStep1() {
    if (!cardFile) {
        showToast("Please upload the Aadhaar Document first.", "error");
        return;
    }

    setLoadingState(true, "ANALYZING DOCUMENT...", "Extracting OCR data...");

    const formData = new FormData();
    formData.append("file", cardFile);

    try {
        const response = await fetch('/api/analyze-card', { method: 'POST', body: formData });
        const data = await response.json();

        if (data.is_aadhaar) {
            // SUCCESS
            displayIntermediateData(data);
            showToast("Aadhaar Detected! Please verify data and proceed.", "success");
        } else {
            // FAILURE
            setLoadingState(false); 
            showToast(data.message || "Document is not a valid Aadhaar.", "error");
        }

    } catch (error) {
        console.error(error);
        setLoadingState(false);
        showToast("Network Error during analysis.", "error");
    }
}

// Helper: Show Data + "Verify QR" Button
function displayIntermediateData(data) {
    const scanIdle = document.getElementById('scan-idle');
    const scanLoader = document.getElementById('scan-loader');
    const resultsGrid = document.getElementById('scan-results');
    const step1Btn = document.getElementById('step1-btn');
    const step2Btn = document.getElementById('step2-btn');
    const verdictBanner = document.getElementById('verdict-section');

    // UI State
    if(scanIdle) scanIdle.classList.add('hidden');
    if(scanLoader) scanLoader.classList.add('hidden');
    if(resultsGrid) resultsGrid.classList.remove('hidden');
    
    // Hide Verdict initially
    if(verdictBanner) verdictBanner.classList.add('hidden');

    // Show correct buttons
    if(step1Btn) step1Btn.classList.remove('hidden');
    if(step2Btn) step2Btn.classList.add('hidden');

    // Populate Fields
    const extracted = data.extracted_data || {};
    updateField('res-name', extracted.name || "NOT DETECTED");
    updateField('res-uid', extracted.aadhaar_number || "xxxx xxxx xxxx");
    updateField('res-dob', extracted.dob || "--/--/----");
    updateField('res-gender', extracted.gender || "--");
}

// --- TRANSITION TO STEP 2 (Prepare QR Upload) ---
function prepareStep2() {
    currentStep = 2;

    // Reset Left Box
    const previewImg = document.getElementById('image-preview');
    const placeholder = document.getElementById('upload-placeholder');
    const clearBtn = document.getElementById('clear-image-btn');
    const uploadTitle = document.getElementById('upload-title');
    const uploadDesc = document.getElementById('upload-desc');
    const uploadIcon = document.getElementById('upload-icon');
    const actionBtn = document.getElementById('action-btn');
    const fileInput = document.getElementById('cardInput');

    fileInput.value = '';
    previewImg.src = "";
    previewImg.classList.add('hidden');
    placeholder.classList.remove('hidden');
    clearBtn.classList.add('hidden');

    uploadIcon.className = "fas fa-qrcode";
    uploadTitle.innerText = "Upload QR Code";
    uploadDesc.innerText = "Please upload the cropped QR code image";
    
    actionBtn.innerText = "Verify QR & Finalize";
    
    // Reset Right Box to Idle
    const scanIdle = document.getElementById('scan-idle');
    const resultsGrid = document.getElementById('scan-results');
    const scanStatus = document.getElementById('scan-status-text');

    resultsGrid.classList.add('hidden'); 
    scanIdle.classList.remove('hidden'); 
    scanStatus.innerText = "Awaiting QR Code input for final verification...";
    
    showToast("Please upload the QR Code.", "success");
}

// --- STEP 2: VERIFY QR & FINALIZE ---
async function executeStep2() {
    if (!qrFile) {
        showToast("Please upload the QR Code image.", "error");
        return;
    }

    setLoadingState(true, "FINALIZING AUDIT...", "Cross-referencing QR data...");

    const formData = new FormData();
    formData.append("file", cardFile);    
    formData.append("qr_file", qrFile);   

    try {
        const response = await fetch('/api/verify-full', { method: 'POST', body: formData });
        const data = await response.json();
        
        displayFinalVerdict(data);

    } catch (error) {
        console.error(error);
        setLoadingState(false);
        showToast("Error during final verification.", "error");
    }
}

// --- FINAL VERDICT DISPLAY ---
function displayFinalVerdict(data) {
    const scanLoader = document.getElementById('scan-loader');
    const resultsGrid = document.getElementById('scan-results');
    const verdictBanner = document.getElementById('verdict-section');
    const dataContainer = document.getElementById('ocr-data-container'); // Optional wrapper if you used it
    
    const step1Btn = document.getElementById('step1-btn'); 
    const step2Btn = document.getElementById('step2-btn'); 
    
    const finalStatus = document.getElementById('final-status');
    const confScore = document.getElementById('confidence-score');

    if(scanLoader) scanLoader.classList.add('hidden');
    if(resultsGrid) resultsGrid.classList.remove('hidden');
    
    // Reveal Verdict
    if(verdictBanner) verdictBanner.classList.remove('hidden');

    // Switch Buttons
    if(step1Btn) step1Btn.classList.add('hidden');    
    if(step2Btn) step2Btn.classList.remove('hidden'); 

    // Status Logic
    const decision = data.final_decision.final_decision; 
    finalStatus.innerText = decision;
    finalStatus.className = "";
    
    if (decision === "ACCEPTED") {
        finalStatus.classList.add("status-accepted");
        // Ensure data is visible if accepted
        const groups = document.querySelectorAll('.data-field-row');
        groups.forEach(g => g.style.display = 'flex');
    } 
    else {
        // Hide Data if Suspicious/Fraud
        if (decision === "FRAUD" || decision === "REJECTED") {
            finalStatus.classList.add("status-rejected");
        } else {
            finalStatus.classList.add("status-suspicious");
        }
        
        // Hide extracted data rows for privacy/security
        const groups = document.querySelectorAll('.data-field-row');
        groups.forEach(g => g.style.display = 'none');
    }

    // Score
    let prob = data.fraud_ml ? data.fraud_ml.fraud_probability : 0;
    let confidence = ((1 - prob) * 100).toFixed(1);
    confScore.innerText = `${confidence}%`;
}

// =========================================================
// 5. HELPER UTILS
// =========================================================

function setLoadingState(isLoading, mainText, subText) {
    const scanIdle = document.getElementById('scan-idle');
    const scanLoader = document.getElementById('scan-loader');
    const loaderText = document.getElementById('loader-text');
    const loaderSub = document.getElementById('loader-subtext');
    const resultsGrid = document.getElementById('scan-results');

    if (isLoading) {
        if(scanIdle) scanIdle.classList.add('hidden');
        if(resultsGrid) resultsGrid.classList.add('hidden');
        if(scanLoader) scanLoader.classList.remove('hidden');
        if(loaderText) loaderText.innerText = mainText;
        if(loaderSub) loaderSub.innerText = subText;
    } else {
        if(scanLoader) scanLoader.classList.add('hidden');
    }
}

function updateField(id, text) {
    const el = document.getElementById(id);
    if (el) el.innerText = text;
}

function showToast(msg, type = 'error') {
    const toast = document.getElementById('error-toast');
    const msgSpan = document.getElementById('error-msg');
    const icon = toast ? toast.querySelector('i') : null;

    if (toast && msgSpan) {
        msgSpan.innerText = msg;
        toast.className = 'error-toast hidden'; // Reset
        
        if (type === 'success') {
            toast.classList.add('success-mode');
            if(icon) icon.className = 'fas fa-check-circle';
        } else {
            if(icon) icon.className = 'fas fa-exclamation-triangle';
        }

        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 4000);
    } else {
        alert(msg);
    }
}
// =========================================================
// 6. LOOKUP FUNCTIONALITY (Add this at the bottom of script.js)
// =========================================================

// 1. Toggle Function (Hides the link, Shows the input box)
function toggleLookupUI() {
    const link = document.getElementById('lookup-link');
    const box = document.getElementById('lookup-box');
    
    if(link) link.classList.add('hidden');
    if(box) box.classList.remove('hidden');
}

// 2. Lookup Logic (Simulates fetching verified data)
async function performLookup() {
    const uidInput = document.getElementById('lookup-input');
    const uid = uidInput.value.trim();

    // 1. Client-Side Validation (12 Digits)
    if (!/^\d{12}$/.test(uid)) {
        showToast("Please enter a valid 12-digit Aadhaar number.", "error");
        return;
    }

    setLoadingState(true, "SEARCHING DATABASE...", "Checking verified records...");

    try {
        // Call Python Backend
        const response = await fetch('/api/lookup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ aadhaar_number: uid })
        });
        
        const result = await response.json();

        if (result.success && result.found) {
            // FOUND: Show Data
            const user = result.data;
            
            document.getElementById('res-name').innerText = user.name || "N/A";
            document.getElementById('res-uid').innerText = user.aadhaar_number || "N/A";
            document.getElementById('res-dob').innerText = user.dob || "N/A";
            document.getElementById('res-gender').innerText = user.gender || "N/A";
            
            // Format data to match display function structure
            const displayData = {
                final_decision: { final_decision: user.status },
                fraud_ml: { fraud_probability: 1 - (user.confidence / 100) },
                ocr_extracted: {
                    name: user.name,
                    aadhaar_number: user.aadhaar_number,
                    dob: user.dob,
                    gender: user.gender
                }
            };
            
            setLoadingState(false);
            displayFinalVerdict(displayData);
            showToast("Record found in database!", "success");
            
        } else {
            // NOT FOUND
            setLoadingState(false);
            showToast("Aadhaar is not verified.", "error");
            
            // Optional: Reset UI to idle
            const scanIdle = document.getElementById('scan-idle');
            const resultsGrid = document.getElementById('scan-results');
            if(resultsGrid) resultsGrid.classList.add('hidden');
            if(scanIdle) scanIdle.classList.remove('hidden');
        }

    } catch (error) {
        console.error(error);
        setLoadingState(false);
        showToast("Server error during lookup.", "error");
    }
}