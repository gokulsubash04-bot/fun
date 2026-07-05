document.addEventListener('DOMContentLoaded', () => {
    // --- State Variables ---
    let currentFileId = null;
    let currentStyle = 'watercolor';
    let isDraggingSlider = false;

    // --- DOM Selectors ---
    const dropZone = document.getElementById('drop-zone');
    const imageInput = document.getElementById('image-input');
    const browseBtn = document.getElementById('browse-btn');
    const styleCardWrapper = document.getElementById('style-card-wrapper');
    const uploadPreviewContainer = document.getElementById('upload-preview-container');
    const previewFileName = document.getElementById('preview-file-name');
    const previewFileSize = document.getElementById('preview-file-size');
    const removeImgBtn = document.getElementById('remove-img-btn');
    const renderBtn = document.getElementById('render-btn');
    const resetParamsBtn = document.getElementById('reset-params-btn');
    const downloadBtn = document.getElementById('download-btn');
    
    const styleOptions = document.querySelectorAll('.style-option');
    const brightnessSlider = document.getElementById('brightness-slider');
    const brightnessVal = document.getElementById('brightness-val');
    const contrastSlider = document.getElementById('contrast-slider');
    const contrastVal = document.getElementById('contrast-val');
    
    // Viewport Elements
    const viewportEmpty = document.getElementById('viewport-empty');
    const viewportDisplay = document.getElementById('viewport-display');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingStatusText = document.getElementById('loading-status-text');
    
    // Comparison Slider Elements
    const comparisonContainer = document.getElementById('comparison-container');
    const processedImage = document.getElementById('processed-image');
    const originalImage = document.getElementById('original-image');
    const originalImageWrapper = document.getElementById('original-image-wrapper');
    const sliderHandle = document.getElementById('slider-handle');

    // Dynamic Parameter Groups
    const paramGroup1 = document.getElementById('param-group-1');
    const paramLabel1 = document.getElementById('param-label-1');
    const paramSlider1 = document.getElementById('param-slider-1');
    const paramVal1 = document.getElementById('param-val-1');

    const paramGroup2 = document.getElementById('param-group-2');
    const paramLabel2 = document.getElementById('param-label-2');
    const paramSlider2 = document.getElementById('param-slider-2');
    const paramVal2 = document.getElementById('param-val-2');

    const paramGroup3 = document.getElementById('param-group-3');
    const paramLabel3 = document.getElementById('param-label-3');
    const paramSlider3 = document.getElementById('param-slider-3');
    const paramVal3 = document.getElementById('param-val-3');

    // --- Loading Status Messages ---
    const loadingPhrases = {
        'upload': ['Scanning photo details...', 'Stretching the digital canvas...', 'Preparing paint brushes...'],
        'watercolor': ['Mixing water and pigments...', 'Applying light washes...', 'Creating paint bleeds...', 'Smoothing edges...'],
        'oil': ['Squeezing oil tubes...', 'Layering heavy brush strokes...', 'Enhancing textures...', 'Waiting for paint to dry...'],
        'cartoon': ['Tracing key outlines...', 'Applying flat color cells...', 'Boosting color contrast...', 'Polishing shading...'],
        'pencil': ['Sharpening graphite pencils...', 'Cross-hatching shadows...', 'Applying paper texture...', 'Smudging edges...'],
        'palette': ['Selecting color palette...', 'Applying thick paint layers...', 'Carving highlights...', 'Adding knife textures...']
    };

    let loadingMessageInterval = null;

    function startLoadingMessages(type) {
        const phrases = loadingPhrases[type] || ['Creating artwork...'];
        let idx = 0;
        loadingStatusText.textContent = phrases[idx];
        
        clearInterval(loadingMessageInterval);
        loadingMessageInterval = setInterval(() => {
            idx = (idx + 1) % phrases.length;
            loadingStatusText.textContent = phrases[idx];
        }, 2200);
    }

    function stopLoadingMessages() {
        clearInterval(loadingMessageInterval);
    }

    // --- Dynamic Slider Configurations ---
    const styleConfigs = {
        watercolor: {
            p1: { show: true, label: 'Brush Size', min: 10, max: 200, step: 5, val: 60 },
            p2: { show: true, label: 'Smoothing Intensity', min: 0.05, max: 1.0, step: 0.05, val: 0.3 },
            p3: { show: false }
        },
        oil: {
            p1: { show: true, label: 'Brush Diameter', min: 1, max: 12, step: 1, val: 4 },
            p2: { show: true, label: 'Color Intensity', min: 1, max: 15, step: 1, val: 3 },
            p3: { show: false }
        },
        cartoon: {
            p1: { show: true, label: 'Color Smoothness', min: 1, max: 10, step: 1, val: 4 },
            p2: { show: true, label: 'Outline Thickness', min: 3, max: 25, step: 2, val: 9 },
            p3: { show: true, label: 'Outline Darkness', min: 1, max: 20, step: 1, val: 5 }
        },
        palette_knife: {
            p1: { show: true, label: 'Color Count (K-Means)', min: 3, max: 24, step: 1, val: 8 },
            p2: { show: true, label: 'Blending Passes', min: 1, max: 10, step: 1, val: 5 },
            p3: { show: false }
        },
        pencil_color: {
            p1: { show: true, label: 'Brush Stroke Size', min: 10, max: 200, step: 5, val: 60 },
            p2: { show: true, label: 'Texture Smoothing', min: 0.01, max: 0.20, step: 0.01, val: 0.07 },
            p3: { show: true, label: 'Graphite Shading', min: 0.01, max: 0.10, step: 0.01, val: 0.03 }
        },
        pencil_gray: {
            p1: { show: true, label: 'Brush Stroke Size', min: 10, max: 200, step: 5, val: 60 },
            p2: { show: true, label: 'Texture Smoothing', min: 0.01, max: 0.20, step: 0.01, val: 0.07 },
            p3: { show: true, label: 'Graphite Shading', min: 0.01, max: 0.10, step: 0.01, val: 0.03 }
        }
    };

    function updateStyleSliders(styleName) {
        const config = styleConfigs[styleName];
        if (!config) return;

        // Parameter 1
        if (config.p1.show) {
            paramGroup1.classList.remove('hidden');
            paramLabel1.textContent = config.p1.label;
            paramSlider1.min = config.p1.min;
            paramSlider1.max = config.p1.max;
            paramSlider1.step = config.p1.step;
            paramSlider1.value = config.p1.val;
            paramVal1.textContent = config.p1.val;
        } else {
            paramGroup1.classList.add('hidden');
        }

        // Parameter 2
        if (config.p2.show) {
            paramGroup2.classList.remove('hidden');
            paramLabel2.textContent = config.p2.label;
            paramSlider2.min = config.p2.min;
            paramSlider2.max = config.p2.max;
            paramSlider2.step = config.p2.step;
            paramSlider2.value = config.p2.val;
            paramVal2.textContent = config.p2.val;
        } else {
            paramGroup2.classList.add('hidden');
        }

        // Parameter 3
        if (config.p3.show) {
            paramGroup3.classList.remove('hidden');
            paramLabel3.textContent = config.p3.label;
            paramSlider3.min = config.p3.min;
            paramSlider3.max = config.p3.max;
            paramSlider3.step = config.p3.step;
            paramSlider3.value = config.p3.val;
            paramVal3.textContent = config.p3.val;
        } else {
            paramGroup3.classList.add('hidden');
        }
    }

    // --- General Event Listeners for UI Sliders ---
    [paramSlider1, paramSlider2, paramSlider3].forEach((slider, idx) => {
        slider.addEventListener('input', (e) => {
            const valSpan = document.getElementById(`param-val-${idx + 1}`);
            if (valSpan) valSpan.textContent = e.target.value;
        });
    });

    brightnessSlider.addEventListener('input', (e) => {
        brightnessVal.textContent = e.target.value;
    });

    contrastSlider.addEventListener('input', (e) => {
        contrastVal.textContent = e.target.value;
    });

    // Reset parameters trigger
    resetParamsBtn.addEventListener('click', () => {
        brightnessSlider.value = 0;
        brightnessVal.textContent = 0;
        contrastSlider.value = 0;
        contrastVal.textContent = 0;
        
        // Reset current style configs to defaults
        const config = styleConfigs[currentStyle];
        if (config) {
            if (config.p1.show) { paramSlider1.value = config.p1.val; paramVal1.textContent = config.p1.val; }
            if (config.p2.show) { paramSlider2.value = config.p2.val; paramVal2.textContent = config.p2.val; }
            if (config.p3.show) { paramSlider3.value = config.p3.val; paramVal3.textContent = config.p3.val; }
        }
    });

    // --- File Drag & Drop Actions ---
    browseBtn.addEventListener('click', () => imageInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragging');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragging');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragging');
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    imageInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    removeImgBtn.addEventListener('click', () => {
        currentFileId = null;
        imageInput.value = '';
        
        // Reset view states
        uploadPreviewContainer.classList.add('hidden');
        dropZone.classList.remove('hidden');
        styleCardWrapper.classList.add('disabled-card');
        renderBtn.disabled = true;
        
        viewportDisplay.classList.add('hidden');
        viewportEmpty.classList.remove('hidden');
        
        downloadBtn.removeAttribute('href');
    });

    // --- File Upload API communication ---
    function handleFileUpload(file) {
        if (!file.type.match('image.*')) {
            alert('Please select a valid image file (JPG, PNG).');
            return;
        }

        const formData = new FormData();
        formData.append('image', file);

        // Show uploading state
        loadingOverlay.classList.remove('hidden');
        startLoadingMessages('upload');

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Upload failed'); });
            }
            return response.json();
        })
        .then(data => {
            currentFileId = data.file_id;
            
            // Set details in preview panel
            previewFileName.textContent = file.name;
            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            previewFileSize.textContent = `${sizeMB} MB`;
            
            dropZone.classList.add('hidden');
            uploadPreviewContainer.classList.remove('hidden');
            
            // Enable Style card and Render button
            styleCardWrapper.classList.remove('disabled-card');
            renderBtn.disabled = false;
            
            // Set sources for display
            originalImage.src = data.original_url;
            processedImage.src = data.original_url; // Default to original before rendering
            
            // Switch viewports
            viewportEmpty.classList.add('hidden');
            viewportDisplay.classList.remove('hidden');
            
            // Reset position slider
            setSliderPosition(50);
            
            // Wait for image loading to sync dimensions
            processedImage.onload = () => {
                syncImageSizes();
                stopLoadingMessages();
                loadingOverlay.classList.add('hidden');
                
                // Automatically perform initial rendering
                processImage();
            };
        })
        .catch(err => {
            stopLoadingMessages();
            loadingOverlay.classList.add('hidden');
            alert(`Error: ${err.message}`);
        });
    }

    // --- Painting Style Selection Events ---
    styleOptions.forEach(opt => {
        opt.addEventListener('click', () => {
            styleOptions.forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            
            currentStyle = opt.dataset.style;
            updateStyleSliders(currentStyle);
        });
    });

    // --- Core Processing Trigger (Process Image) ---
    renderBtn.addEventListener('click', () => {
        processImage();
    });

    function processImage() {
        if (!currentFileId) return;

        loadingOverlay.classList.remove('hidden');
        startLoadingMessages(currentStyle.includes('pencil') ? 'pencil' : currentStyle);

        // Gather payloads
        const payload = {
            file_id: currentFileId,
            style: currentStyle,
            brightness: brightnessSlider.value,
            contrast: contrastSlider.value
        };

        // Inject custom style parameters
        const config = styleConfigs[currentStyle];
        if (config.p1.show) {
            // Map parameter key to payload
            const key = currentStyle === 'cartoon' ? 'smoothness' : 'brush_size';
            payload[key] = paramSlider1.value;
        }
        if (config.p2.show) {
            const key = currentStyle === 'cartoon' ? 'edge_thickness' : (currentStyle === 'palette_knife' ? 'smoothness' : 'smoothing');
            payload[key] = paramSlider2.value;
        }
        if (config.p3.show) {
            const key = currentStyle === 'cartoon' ? 'edge_strength' : 'shade_factor';
            payload[key] = paramSlider3.value;
        }

        fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Stylization failed'); });
            }
            return response.json();
        })
        .then(data => {
            // Update image sources
            processedImage.src = data.processed_url;
            downloadBtn.href = data.processed_url;
            
            // Reload original image preview mapping
            processedImage.onload = () => {
                syncImageSizes();
                stopLoadingMessages();
                loadingOverlay.classList.add('hidden');
            };
        })
        .catch(err => {
            stopLoadingMessages();
            loadingOverlay.classList.add('hidden');
            alert(`Stylization error: ${err.message}`);
        });
    }

    // --- Before/After Image Comparator Logic ---
    
    function setSliderPosition(percentage) {
        percentage = Math.max(0, Math.min(100, percentage));
        sliderHandle.style.left = `${percentage}%`;
        originalImageWrapper.style.width = `${percentage}%`;
    }

    function handleSliderMove(clientX) {
        const rect = comparisonContainer.getBoundingClientRect();
        const offsetX = clientX - rect.left;
        const percentage = (offsetX / rect.width) * 100;
        setSliderPosition(percentage);
    }

    // Touch and mouse dragging handlers
    sliderHandle.addEventListener('mousedown', (e) => {
        isDraggingSlider = true;
        e.preventDefault();
    });

    comparisonContainer.addEventListener('mousedown', (e) => {
        // If clicking on the container, jump slider to click point
        if (e.target !== sliderHandle && !sliderHandle.contains(e.target)) {
            handleSliderMove(e.clientX);
        }
    });

    window.addEventListener('mouseup', () => {
        isDraggingSlider = false;
    });

    window.addEventListener('mousemove', (e) => {
        if (!isDraggingSlider) return;
        handleSliderMove(e.clientX);
    });

    // Mobile touch events
    sliderHandle.addEventListener('touchstart', (e) => {
        isDraggingSlider = true;
    });

    window.addEventListener('touchend', () => {
        isDraggingSlider = false;
    });

    window.addEventListener('touchmove', (e) => {
        if (!isDraggingSlider) return;
        if (e.touches.length > 0) {
            handleSliderMove(e.touches[0].clientX);
        }
    });

    // Align original and processed layers perfectly
    function syncImageSizes() {
        if (!processedImage.complete || processedImage.src === '') return;
        
        // Match original image size and absolute offsets to the rendered processed image size
        const rect = processedImage.getBoundingClientRect();
        const containerRect = comparisonContainer.getBoundingClientRect();
        
        // Calculate offset difference inside container
        const leftOffset = processedImage.offsetLeft;
        const topOffset = processedImage.offsetTop;
        
        originalImage.style.width = `${processedImage.clientWidth}px`;
        originalImage.style.height = `${processedImage.clientHeight}px`;
        originalImage.style.left = `${leftOffset}px`;
        originalImage.style.top = `${topOffset}px`;
        originalImage.style.position = 'absolute';
        originalImage.style.maxWidth = 'none';
        originalImage.style.maxHeight = 'none';
    }

    // Sync on window resizing to avoid alignment drifting
    window.addEventListener('resize', () => {
        if (currentFileId) {
            syncImageSizes();
        }
    });
    
    // Add interval observer check to ensure alignments stay locked if layout changes
    setInterval(() => {
        if (currentFileId) {
            syncImageSizes();
        }
    }, 1000);
});
