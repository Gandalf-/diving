const MAX_PLAYING_VIDEOS = 5;
const PLAY_DELAY_MS = 500;
const DEBOUNCE_DELAY_MS = 100;

let playingVideos = [];
let isHandling = false;
let debounceTimer;

function isElementInViewport(el) {
  const rect = el.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}

function stopVideo(video) {
  video.pause();
  video.currentTime = 0;
  playingVideos = playingVideos.filter((v) => v !== video);
}

function playVideo(video) {
  if (playingVideos.length >= MAX_PLAYING_VIDEOS) {
    stopVideo(playingVideos[0]);
  }
  video.play().catch((error) => console.error('Error playing video:', error));
  playingVideos.push(video);
}

function handleVisibleVideos() {
  if (isHandling) return;
  isHandling = true;

  const allVideos = document.querySelectorAll('video.clip');
  const visibleVideos = Array.from(allVideos).filter(isElementInViewport);

  // Stop videos that are no longer visible
  playingVideos.forEach((video) => {
    if (!visibleVideos.includes(video)) {
      stopVideo(video);
    }
  });

  // Play visible videos that aren't already playing
  visibleVideos.forEach((video, index) => {
    if (!playingVideos.includes(video) && playingVideos.length < MAX_PLAYING_VIDEOS) {
      setTimeout(() => {
        playVideo(video);
        if (index === visibleVideos.length - 1) {
          isHandling = false;
        }
      }, index * PLAY_DELAY_MS);
    } else if (index === visibleVideos.length - 1) {
      isHandling = false;
    }
  });

  if (visibleVideos.length === 0) {
    isHandling = false;
  }
}

function debouncedHandleVisibleVideos() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(handleVisibleVideos, DEBOUNCE_DELAY_MS);
}

function initializeVideoHandling() {
  handleVisibleVideos();
  window.addEventListener('scroll', debouncedHandleVisibleVideos);
  window.addEventListener('resize', debouncedHandleVisibleVideos);
}

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initializeVideoHandling);

// Re-initialize when new content is loaded
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
      debouncedHandleVisibleVideos();
    }
  });
});

observer.observe(document.body, { childList: true, subtree: true });
