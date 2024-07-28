// Configuration
const INITIAL_LOAD_COUNT = 3;
const LOAD_BATCH_SIZE = 3;
const LOAD_THRESHOLD = 200; // pixels from bottom of page to trigger load

// State
let currentIndex = 0;
let isLoading = false;

// Utility functions
function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

async function loadTimelineContent(url) {
    try {
        const response = await fetch(url);
        const content = await response.text();
        const div = document.createElement('div');
        div.className = 'timeline-item isloaded';
        div.innerHTML = content;
        return div;
    } catch (error) {
        console.error('Error loading timeline content:', error);
        const errorDiv = document.createElement('div');
        errorDiv.innerHTML = '<p>Error loading content. Please try again later.</p>';
        return errorDiv;
    }
}

async function loadMoreContent() {
    if (isLoading || currentIndex >= timelineUrls.length) return;

    isLoading = true;
    const fragment = document.createDocumentFragment();

    const loadPromises = [];
    for (let i = 0; i < LOAD_BATCH_SIZE && currentIndex < timelineUrls.length; i++) {
        const url = timelineUrls[currentIndex];
        loadPromises.push(loadTimelineContent(url));
        currentIndex++;
    }

    const loadedElements = await Promise.all(loadPromises);
    loadedElements.forEach(element => fragment.appendChild(element));

    document.querySelector('.wrapper').appendChild(fragment);
    isLoading = false;
}

function handleScroll() {
    if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - LOAD_THRESHOLD) {
        loadMoreContent();
    }
}

// Initialization
async function initializeTimeline() {
    for (let i = 0; i < INITIAL_LOAD_COUNT; i++) {
        await loadMoreContent();
    }
    window.addEventListener('scroll', handleScroll);
}

document.addEventListener('DOMContentLoaded', initializeTimeline);
