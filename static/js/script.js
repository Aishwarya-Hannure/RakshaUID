// --- GLOBAL VARIABLES ---
let currentStep = 1; 
let cardFile = null;
let qrFile = null;
let savedAadhaarFilename = null; 
let cameraStream = null;

document.addEventListener('DOMContentLoaded', () => {
    
    // =========================================================
    // 1. THEME RESTORATION (Works on ALL pages)
    // =========================================================
    const toggleBtn = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    const icon = toggleBtn ? toggleBtn.querySelector('i') : null;

    const savedTheme = localStorage.getItem('theme') || 'light';
    htmlElement.setAttribute('data-theme', savedTheme);
    if (icon) icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';

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
    // 2. AUTHENTICATION LOGIC (Added to fix Login/Signup)
    // =========================================================
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const messageDiv = document.getElementById('message');

    function showAuthMessage(type, text) {
        if(messageDiv) {
            messageDiv.className = `message ${type}`;
            messageDiv.innerText = text;
            messageDiv.classList.remove('hidden');
        }
    }

    // --- LOGIN HANDLER ---
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault(); 
            const formData = new FormData(loginForm);
            const data = Object.fromEntries(formData.entries());
            
            // Handle "Remember Me" if present
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
                showAuthMessage('error', 'Server connection failed.');
            }
        });
    }

    // --- SIGNUP HANDLER ---
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
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
                showAuthMessage('error', 'Server connection failed.');
            }
        });
    }

    // =========================================================
    // 3. DASHBOARD LOGIC (Wrapped to prevent Login Page Crash)
    // =========================================================
    const fileInput = document.getElementById('cardInput');
    
    // Only run this if we are on the dashboard page
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;

            if (currentStep === 1) {
                // STEP 1: Upload Aadhaar
                cardFile = file;
                showPreview(file);
            } else if (currentStep === 2) {
                // STEP 2: Upload Face
                showPreview(file);
                uploadFaceForVerification(file);
            } else if (currentStep === 3) {
                // STEP 3: Upload QR
                qrFile = file;
                showPreview(file);
            }
        });

        const dropZone = document.getElementById('drop-zone');
        if (dropZone) {
            dropZone.addEventListener('click', () => {
                if (currentStep !== 2) fileInput.click();
            });
        }

        const clearBtn = document.getElementById('clear-image-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                resetUploadZone();
            });
        }

        // --- FACE BUTTONS ---
        const btnUploadFace = document.getElementById('btn-upload-face');
        if (btnUploadFace) {
            btnUploadFace.addEventListener('click', (e) => {
                e.stopPropagation();
                fileInput.click();
            });
        }

        const btnOpenCamera = document.getElementById('btn-open-camera');
        if (btnOpenCamera) {
            btnOpenCamera.addEventListener('click', (e) => {
                e.stopPropagation();
                startCamera();
            });
        }

        const btnCaptureFace = document.getElementById('btn-capture-face');
        if (btnCaptureFace) {
            btnCaptureFace.addEventListener('click', (e) => {
                e.stopPropagation();
                capturePhoto();
            });
        }
    }
});

// =========================================================
// 4. MAIN EXECUTION FLOW
// =========================================================
async function handleExecution() {
    if (currentStep === 1) {
        await executeStep1();
    } else if (currentStep === 2) {
        showToast("Please use the buttons inside the box to verify face.", "error");
    } else if (currentStep === 3) {
        await executeStep3();
    }
}

// =========================================================
// STEP 1: ANALYZE AADHAAR
// =========================================================
async function executeStep1() {
    if (!cardFile) return showToast("Please upload the Aadhaar Document first.", "error");

    setLoadingState(true, "ANALYZING DOCUMENT...", "Extracting OCR data...");
    const formData = new FormData();
    formData.append("file", cardFile);

    try {
        const response = await fetch('/api/analyze-card', { method: 'POST', body: formData });
        const data = await response.json();

        if (data.is_aadhaar) {
            savedAadhaarFilename = data.aadhaar_path; 
            displayIntermediateData(data);
            showToast("Aadhaar Detected! Proceeding to Face Verification.", "success");
            prepareStep2_Face(); 
        } else {
            setLoadingState(false);
            showToast(data.message || "Document is not a valid Aadhaar.", "error");
        }
    } catch (error) {
        console.error(error);
        setLoadingState(false);
        showToast("Network Error during analysis.", "error");
    }
}

// =========================================================
// STEP 2: FACE VERIFICATION UI & LOGIC
// =========================================================
function prepareStep2_Face() {
    currentStep = 2;
    setLoadingState(false);
    
    document.getElementById('image-preview').classList.add('hidden');
    document.getElementById('upload-placeholder').classList.add('hidden');
    document.getElementById('clear-image-btn').classList.add('hidden');
    
    document.getElementById('upload-title').innerText = "Biometric Verification";
    document.getElementById('upload-desc').innerText = "Verify Person's Face against Aadhaar";
    document.getElementById('upload-icon').className = "fas fa-user-lock";

    document.getElementById('face-options').classList.remove('hidden');
    document.getElementById('action-btn').classList.add('hidden');
}

// --- Camera Logic ---
async function startCamera() {
    const video = document.getElementById('camera-stream');
    const placeholder = document.getElementById('upload-placeholder');
    
    placeholder.classList.add('hidden');
    document.getElementById('image-preview').classList.add('hidden');
    video.classList.remove('hidden');
    
    document.getElementById('btn-open-camera').classList.add('hidden');
    document.getElementById('btn-upload-face').classList.add('hidden');
    document.getElementById('btn-capture-face').classList.remove('hidden');

    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = cameraStream;
    } catch (err) {
        showToast("Camera permission denied.", "error");
        resetUploadZone();
    }
}

function capturePhoto() {
    const video = document.getElementById('camera-stream');
    const canvas = document.getElementById('camera-canvas');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    if(cameraStream) cameraStream.getTracks().forEach(track => track.stop());
    video.classList.add('hidden');
    document.getElementById('btn-capture-face').classList.add('hidden');

    const imgPreview = document.getElementById('image-preview');
    imgPreview.src = canvas.toDataURL('image/jpeg');
    imgPreview.classList.remove('hidden');

    canvas.toBlob((blob) => {
        const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
        uploadFaceForVerification(file);
    }, 'image/jpeg');
}

// --- Face API Call with 4-Second Delay ---
async function uploadFaceForVerification(file) {
    setLoadingState(true, "VERIFYING BIOMETRICS...", "Running Facial Recognition...");
    document.getElementById('face-options').classList.add('hidden');

    const formData = new FormData();
    formData.append("person_image", file);
    formData.append("aadhaar_filename", savedAadhaarFilename);

    try {
        const response = await fetch('/api/verify-face', { method: 'POST', body: formData });
        const data = await response.json();

        if (data.success) {
            // STOP LOADING, SHOW TOAST
            setLoadingState(false);
            showToast(`Match Found! (Score: ${data.score}%) Redirecting in 4s...`, "success");
            
            // --- 4 SECOND DELAY HERE ---
            setTimeout(() => {
                prepareStep3_QR();
            }, 4000); 

        } else {
            setLoadingState(false);
            showToast(data.message, "error");
            prepareStep2_Face(); 
        }
    } catch (e) {
        setLoadingState(false);
        showToast("Error processing biometrics.", "error");
        prepareStep2_Face();
    }
}

// =========================================================
// STEP 3: QR CODE
// =========================================================
function prepareStep3_QR() {
    currentStep = 3;
    setLoadingState(false);
    resetUploadZone(); 

    document.getElementById('upload-title').innerText = "Upload QR Code";
    document.getElementById('upload-desc').innerText = "Please upload the cropped QR code image";
    document.getElementById('upload-icon').className = "fas fa-qrcode";
    
    document.getElementById('face-options').classList.add('hidden');

    const actionBtn = document.getElementById('action-btn');
    actionBtn.innerText = "Verify QR & Finalize";
    actionBtn.classList.remove('hidden');
    
    document.getElementById('scan-status-text').innerText = "Awaiting QR Code input for final verification...";
    showToast("Face Verified. Now upload QR.", "success");
}

async function executeStep3() {
    if (!qrFile) return showToast("Please upload the QR Code image.", "error");

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

// =========================================================
// HELPER UTILS
// =========================================================
function showPreview(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const img = document.getElementById('image-preview');
        img.src = e.target.result;
        img.classList.remove('hidden');
        document.getElementById('upload-placeholder').classList.add('hidden');
        document.getElementById('clear-image-btn').classList.remove('hidden');
    };
    reader.readAsDataURL(file);
}

function resetUploadZone() {
    document.getElementById('cardInput').value = '';
    document.getElementById('image-preview').classList.add('hidden');
    document.getElementById('image-preview').src = '';
    document.getElementById('camera-stream').classList.add('hidden');
    document.getElementById('upload-placeholder').classList.remove('hidden');
    document.getElementById('clear-image-btn').classList.add('hidden');
    
    if(currentStep === 3) qrFile = null;
}

function setLoadingState(isLoading, mainText, subText) {
    const scanIdle = document.getElementById('scan-idle');
    const scanLoader = document.getElementById('scan-loader');
    const resultsGrid = document.getElementById('scan-results');

    if (isLoading) {
        if(scanIdle) scanIdle.classList.add('hidden');
        if(resultsGrid) resultsGrid.classList.add('hidden');
        if(scanLoader) scanLoader.classList.remove('hidden');
        document.getElementById('loader-text').innerText = mainText;
        document.getElementById('loader-subtext').innerText = subText;
    } else {
        if(scanLoader) scanLoader.classList.add('hidden');
    }
}

function displayIntermediateData(data) {
    const extracted = data.extracted_data || {};
    document.getElementById('scan-idle').classList.add('hidden');
    document.getElementById('scan-results').classList.remove('hidden');
    document.getElementById('verdict-section').classList.add('hidden'); 
    
    updateField('res-name', extracted.name || "NOT DETECTED");
    updateField('res-uid', extracted.aadhaar_number || "xxxx xxxx xxxx");
    updateField('res-dob', extracted.dob || "--/--/----");
    updateField('res-gender', extracted.gender || "--");

    document.getElementById('step2-btn').classList.add('hidden');
}

function displayFinalVerdict(data) {
    const resultsGrid = document.getElementById('scan-results');
    const verdictBanner = document.getElementById('verdict-section');
    const finalStatus = document.getElementById('final-status');
    const confScore = document.getElementById('confidence-score');

    document.getElementById('scan-loader').classList.add('hidden');
    resultsGrid.classList.remove('hidden');
    verdictBanner.classList.remove('hidden');

    const decision = data.final_decision.final_decision;
    finalStatus.innerText = decision;
    
    if (decision === "ACCEPTED") {
        finalStatus.className = "status-accepted";
        document.querySelectorAll('.data-field-row').forEach(g => g.style.display = 'flex');
    } else {
        finalStatus.className = ""; 
        if(decision === "FRAUD" || decision === "REJECTED") finalStatus.classList.add("status-rejected");
        else finalStatus.classList.add("status-suspicious");
        
        document.querySelectorAll('.data-field-row').forEach(g => g.style.display = 'none');
    }

    let prob = data.fraud_ml ? data.fraud_ml.fraud_probability : 0;
    confScore.innerText = `${((1 - prob) * 100).toFixed(1)}%`;
    
    document.getElementById('step2-btn').classList.remove('hidden');
}

function updateField(id, text) {
    const el = document.getElementById(id);
    if (el) el.innerText = text;
}

function showToast(msg, type = 'error') {
    const toast = document.getElementById('error-toast');
    const msgSpan = document.getElementById('error-msg');
    if (toast && msgSpan) {
        msgSpan.innerText = msg;
        toast.className = `error-toast ${type === 'success' ? 'success-mode' : ''}`;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 4000);
    } else alert(msg);
}

// LOOKUP LOGIC
function toggleLookupUI() {
    const link = document.getElementById('lookup-link');
    const box = document.getElementById('lookup-box');
    if(link) link.classList.add('hidden');
    if(box) box.classList.remove('hidden');
}

async function performLookup() {
    const uid = document.getElementById('lookup-input').value.trim();
    if (!/^\d{12}$/.test(uid)) return showToast("Enter 12-digit Aadhaar.", "error");

    setLoadingState(true, "SEARCHING...", "Checking records...");
    try {
        const response = await fetch('/api/lookup', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ aadhaar_number: uid })
        });
        const result = await response.json();
        
        if (result.success && result.found) {
            const user = result.data;
            const displayData = {
                final_decision: { final_decision: user.status },
                fraud_ml: { fraud_probability: 1 - (user.confidence / 100) },
                extracted_data: user 
            };
            displayIntermediateData({ extracted_data: user });
            displayFinalVerdict(displayData);
            showToast("Record found!", "success");
        } else {
            setLoadingState(false);
            showToast("Not verified.", "error");
            document.getElementById('scan-idle').classList.remove('hidden');
        }
    } catch (e) {
        setLoadingState(false);
        showToast("Server error.", "error");
    }
}