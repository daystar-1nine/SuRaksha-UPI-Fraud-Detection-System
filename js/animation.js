/**
 * js/animation.js — Reusable micro-animation utilities
 *
 * Provides lightweight, composable animation helpers used across
 * SuRaksha pages for a premium, consistent feel.
 *
 * Usage (ES module):
 *   import { animCount, fadeIn, pulseOnce, typewriterEffect } from '/js/animation.js';
 */

/**
 * Animated counter that eases from 0 → target over `dur` milliseconds.
 * Uses a cubic ease-out curve for a natural deceleration effect.
 *
 * @param {HTMLElement} el     - Target element to write count into
 * @param {number}      target - Final numeric value
 * @param {number}      dur    - Duration in ms (default 2000)
 * @param {string}      locale - Locale string for toLocaleString (default 'en-IN')
 */
export function animCount(el, target, dur = 2000, locale = "en-IN") {
    if (!el || target == null) return;
    const step = (ts) => {
        if (!step.t0) step.t0 = ts;
        const p = Math.min((ts - step.t0) / dur, 1);
        const ease = 1 - Math.pow(1 - p, 3); // cubic ease-out
        el.textContent = Math.floor(ease * target).toLocaleString(locale);
        if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
}

/**
 * Fades an element in by transitioning opacity from 0 → 1.
 * Adds CSS transition and then triggers reflow before applying opacity.
 *
 * @param {HTMLElement} el       - Element to fade in
 * @param {number}      duration - Transition duration in ms (default 400)
 */
export function fadeIn(el, duration = 400) {
    if (!el) return;
    el.style.transition = `opacity ${duration}ms ease`;
    el.style.opacity = "0";
    requestAnimationFrame(() => {
        requestAnimationFrame(() => { el.style.opacity = "1"; });
    });
}

/**
 * Pulses an element once with a scale-up/down transform to draw attention.
 * Self-cleaning — removes inline style after animation completes.
 *
 * @param {HTMLElement} el - Element to pulse
 */
export function pulseOnce(el) {
    if (!el) return;
    el.style.transition = "transform 0.15s ease, transform 0.3s ease 0.15s";
    el.style.transform = "scale(1.08)";
    setTimeout(() => {
        el.style.transform = "scale(1)";
        setTimeout(() => { el.style.transition = ""; el.style.transform = ""; }, 300);
    }, 150);
}

/**
 * Typewriter effect — writes `text` character-by-character into `el`.
 *
 * @param {HTMLElement} el    - Element to type into
 * @param {string}      text  - Text to type
 * @param {number}      speed - Ms per character (default 40)
 * @returns {Promise<void>} Resolves when typing is complete
 */
export function typewriterEffect(el, text, speed = 40) {
    if (!el) return Promise.resolve();
    el.textContent = "";
    return new Promise((resolve) => {
        let i = 0;
        const tick = () => {
            if (i < text.length) {
                el.textContent += text[i++];
                setTimeout(tick, speed);
            } else {
                resolve();
            }
        };
        tick();
    });
}

/**
 * Scroll-reveal observer — fades + slides elements into view when
 * they enter the viewport. Attach to any elements you want animated.
 *
 * @param {string} selector - CSS selector for elements to observe (default '.fade-in-on-scroll')
 */
export function initScrollReveal(selector = ".fade-in-on-scroll") {
    const obs = new IntersectionObserver((entries) => {
        entries.forEach((e) => {
            if (e.isIntersecting) {
                e.target.classList.add("opacity-100", "translate-y-0");
                obs.unobserve(e.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll(selector).forEach((el) => {
        el.classList.add("opacity-0", "translate-y-4", "transition-all", "duration-700", "ease-out");
        obs.observe(el);
    });
}
