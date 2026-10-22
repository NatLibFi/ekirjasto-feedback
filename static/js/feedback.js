/* Keep submission state free of feedback content and contact information. */
(() => {
    'use strict';

    const form = document.getElementById('feedback-form');
    const prefix = 'ekirjasto-feedback:';
    const cooldown = 60_000;
    const read = (storage, key) => {
        try { return window[storage].getItem(prefix + key); } catch { return null; }
    };
    const write = (storage, key, value) => {
        try { window[storage].setItem(prefix + key, value); } catch { /* Storage may be disabled. */ }
    };
    const remove = (storage, key) => {
        try { window[storage].removeItem(prefix + key); } catch { /* Storage may be disabled. */ }
    };

    const pending = read('sessionStorage', 'pending');
    if (document.body.dataset.page === 'success' && pending) {
        write('sessionStorage', 'sent:' + pending, 'true');
        write('localStorage', 'last-attempt', String(Date.now()));
        remove('sessionStorage', 'pending');
    }
    if (document.body.dataset.page === 'error') {
        remove('sessionStorage', 'pending');
        const back = document.getElementById('return-to-form');
        if (back && window.history.length > 1) {
            back.hidden = false;
            back.addEventListener('click', () => window.history.back());
        }
    }
    if (!form) return;

    const submit = form.querySelector('[type="submit"]');
    const status = form.querySelector('.submission-status');
    const languageButtons = document.querySelectorAll('.language');
    let submitting = false;
    languageButtons.forEach(link => {
        link.addEventListener('click', event => {
            event.preventDefault();
            if (submitting) return;
            const switchLanguage = document.createElement('button');
            switchLanguage.type = 'submit';
            switchLanguage.name = 'change_language';
            switchLanguage.value = link.dataset.previousLanguage;
            switchLanguage.formAction = link.href;
            switchLanguage.formNoValidate = true;
            switchLanguage.hidden = true;
            form.append(switchLanguage);
            form.requestSubmit(switchLanguage);
        });
    });
    let timeout;
    // This identifier survives back/forward navigation without storing form values.
    const formId = window.history.state?.feedbackFormId ||
        (window.crypto?.randomUUID ? window.crypto.randomUUID() : String(Date.now()) + Math.random());
    try {
        window.history.replaceState({ ...window.history.state, feedbackFormId: formId }, '');
    } catch { /* The in-memory guard still prevents double clicks. */ }

    function updateSubmissionState() {
        window.clearTimeout(timeout);
        const alreadySent = read('sessionStorage', 'sent:' + formId) === 'true';
        const elapsed = Date.now() - Number(read('localStorage', 'last-attempt') || 0);
        const remaining = Math.max(0, cooldown - elapsed);
        submit.disabled = submitting || alreadySent || remaining > 0;
        status.textContent = submitting ? status.dataset.sending :
            alreadySent ? status.dataset.sent : remaining > 0 ? status.dataset.wait : '';
        if (remaining > 0 && !alreadySent && !submitting) {
            timeout = window.setTimeout(updateSubmissionState, Math.min(remaining + 50, cooldown));
        }
    }

    form.addEventListener('submit', event => {
        if (submitting) {
            event.preventDefault();
            return;
        }
        if (event.submitter?.name === 'change_language') {
            submitting = true;
            return;
        }
        updateSubmissionState();
        if (submit.disabled) {
            event.preventDefault();
            return;
        }
        submitting = true;
        form.setAttribute('aria-busy', 'true');
        write('sessionStorage', 'pending', formId);
        write('localStorage', 'last-attempt', String(Date.now()));
        languageButtons.forEach(link => { link.setAttribute('aria-disabled', 'true'); });
        updateSubmissionState();
    });
    window.addEventListener('pageshow', () => {
        submitting = false;
        form.removeAttribute('aria-busy');
        languageButtons.forEach(link => { link.removeAttribute('aria-disabled'); });
        updateSubmissionState();
    });
    window.addEventListener('storage', updateSubmissionState);
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) updateSubmissionState();
    });
    updateSubmissionState();

    // Allow the page and the textarea to scroll when the virtual keyboard opens.
    function keepFocusedFieldVisible() {
        const viewport = window.visualViewport;
        const height = viewport ? viewport.height : window.innerHeight;
        const top = viewport ? viewport.offsetTop : 0;
        const inset = Math.max(0, window.innerHeight - height - top);
        document.documentElement.style.setProperty('--visible-height', `${height}px`);
        document.documentElement.style.setProperty('--keyboard-inset', `${inset}px`);
        window.requestAnimationFrame(() => {
            const field = document.activeElement;
            if (!form.contains(field) || !field.matches('input:not([type="hidden"]), textarea, select')) return;
            const bounds = field.getBoundingClientRect();
            const margin = 16;
            if (bounds.bottom > top + height - margin) {
                window.scrollBy(0, bounds.bottom - (top + height - margin));
            } else if (bounds.top < top + margin) {
                window.scrollBy(0, bounds.top - top - margin);
            }
        });
    }
    form.addEventListener('focusin', keepFocusedFieldVisible);
    window.addEventListener('resize', keepFocusedFieldVisible);
    window.visualViewport?.addEventListener('resize', keepFocusedFieldVisible);
    keepFocusedFieldVisible();

    const subject = document.getElementById('subject');
    const feedbackTarget = document.getElementById('feedback_target');
    const acquisitionTypeField = document.getElementById('acquisition_type');
    const feedbackTargetSection = document.getElementById('feedback-target-field');
    const acquisitionSection = document.getElementById('acquisition-type-field');
    const bookDetails = document.getElementById('book-details');
    const bookName = document.getElementById('book_name');
    const bookFormat = document.getElementById('book_format');
    const isAcquisitionSuggestion = () => subject?.value === form.dataset.acquisitionSubject;
    function setRequired(field, required) {
        if (!field) return;
        field.required = required;
        field.setAttribute('aria-required', String(required));
        field.closest('.field')?.querySelector('[data-required-indicator]')?.toggleAttribute('hidden', !required);
    }
    function updateConditionalFields() {
        const isAcquisition = isAcquisitionSuggestion();
        const isBookFeedback = !isAcquisition && feedbackTarget?.value === 'books';
        if (feedbackTargetSection) feedbackTargetSection.hidden = isAcquisition;
        if (acquisitionSection) acquisitionSection.hidden = !isAcquisition;
        if (bookDetails) bookDetails.hidden = !isAcquisition && !isBookFeedback;
        if (bookFormat) bookFormat.closest('.field').hidden = !isBookFeedback;

        setRequired(feedbackTarget, !isAcquisition);
        setRequired(acquisitionTypeField, isAcquisition);
        setRequired(bookName, isBookFeedback);
        setRequired(bookFormat, isBookFeedback);

        if (isAcquisition) {
            if (feedbackTarget) feedbackTarget.value = '';
            if (bookFormat) bookFormat.value = '';
        } else {
            if (acquisitionTypeField) acquisitionTypeField.value = '';
            if (!isBookFeedback) {
                if (bookName) bookName.value = '';
                if (bookFormat) bookFormat.value = '';
            }
        }
        if (isAcquisition && bookName) bookName.required = false;
    }
    subject?.addEventListener('change', updateConditionalFields);
    feedbackTarget?.addEventListener('change', updateConditionalFields);
    updateConditionalFields();

    document.getElementById('form-errors')?.focus();
    if (window.parent !== window && form.dataset.parentOrigin) {
        const token = form.querySelector('[name="csrf_token"]');
        if (token) {
            window.parent.postMessage({ type: 'feedback-csrf-token', csrfToken: token.value }, form.dataset.parentOrigin);
        }
    }
})();
