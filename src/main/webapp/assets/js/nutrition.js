(() => {
    'use strict';

    const attachImageFallback = img => {
        const fallback = () => {
            if (img.dataset.fallbackApplied) return;
            img.dataset.fallbackApplied = 'true';
            img.src = img.dataset.fallback;
        };
        img.addEventListener('error', fallback);
        if (img.complete && img.naturalWidth === 0) fallback();
    };
    document.querySelectorAll('[data-recipe-image]').forEach(attachImageFallback);

    document.querySelectorAll('[data-recipe-form]').forEach(form => {
        const meal = form.querySelector('[data-meal-select]');
        const recipe = form.querySelector('[data-recipe-select]');
        const empty = form.querySelector('[data-empty-recipes]');
        const submit = form.querySelector('button[type="submit"]');
        if (!meal || !recipe) return;

        const sync = () => {
            const selected = recipe.value;
            let first = null;
            let keepSelected = false;
            for (const option of recipe.options) {
                const matches = option.dataset.meal === meal.value;
                option.hidden = !matches;
                option.disabled = !matches;
                if (matches) {
                    if (!first) first = option;
                    if (option.value === selected) keepSelected = true;
                }
            }
            recipe.value = keepSelected ? selected : first ? first.value : '';
            recipe.disabled = !first;
            if (submit) submit.disabled = !first;
            if (empty) empty.hidden = Boolean(first);
        };
        meal.addEventListener('change', sync);
        sync();
    });

    document.querySelectorAll('form[data-confirm]').forEach(form => {
        form.addEventListener('submit', event => {
            if (!window.confirm(form.dataset.confirm)) event.preventDefault();
        });
    });

    let previewBusy = false;
    const integer = value => {
        // Round only for display, from the decimal string supplied by BigDecimal.
        const text = String(value);
        if (!/^-?[0-9]+(?:\.[0-9]+)?$/.test(text)) throw new Error('Invalid decimal');
        const negative = text.startsWith('-');
        const [whole, fraction = ''] = (negative ? text.slice(1) : text).split('.');
        let result = BigInt(whole);
        if (fraction && fraction[0] >= '5') result += 1n;
        return (negative && result !== 0n ? '-' : '') + result.toString();
    };
    const previewButtons = () => [...document.querySelectorAll('[data-swap-form] button, [data-save-suggestion], [data-regenerate]')];
    document.querySelectorAll('[data-swap-form]').forEach(form => {
        form.addEventListener('submit', async event => {
            event.preventDefault();
            if (previewBusy) return;
            previewBusy = true;
            const buttons = previewButtons().map(button => [button, button.disabled]);
            buttons.forEach(([button]) => { button.disabled = true; });
            const status = document.querySelector('[data-swap-status]');
            status.textContent = 'Đang tìm món thay thế…';
            const data = new URLSearchParams(new FormData(form));
            data.set('format', 'json');
            let complete = false;
            try {
                const response = await fetch(form.getAttribute('action'), {method: 'POST', body: data, credentials: 'same-origin'});
                if (!response.ok) throw new Error('Swap rejected');
                const result = await response.json();
                const s = result.suggestion;
                const type = data.get('mealType');
                const meal = s.meals.find(m => m.mealType === type);
                const card = document.querySelector('[data-suggestion-meal="' + type + '"]');
                if (!meal || !card || !result.suggestionToken) throw new Error('Invalid preview');
                // Update this card only. Never replace the two untouched meal cards or journal.
                card.querySelector('[data-meal-name]').textContent = meal.name;
                const image = card.querySelector('[data-recipe-image]');
                delete image.dataset.fallbackApplied;
                image.alt = meal.name;
                image.src = meal.imageUrl;
                card.querySelectorAll('[data-fact]').forEach(node => { node.textContent = integer(meal.nutrition[node.dataset.fact]); });
                document.querySelectorAll('[data-total]').forEach(node => { node.textContent = integer(s.total[node.dataset.total]); });
                for (const [selector, value] of [['[data-target]', s.targetKcal], ['[data-difference]', s.differenceKcal],
                    ['[data-projected]', s.projectedDay.caloriesKcal], ['[data-projected-difference]', s.projectedDifferenceKcal]]) {
                    document.querySelector(selector).textContent = integer(value);
                }
                document.querySelector('[data-exceeds]').hidden = !s.exceedsTarget;
                const warnings = document.querySelector('[data-suggestion-warnings]');
                warnings.replaceChildren(...s.warnings.map(text => {
                    const li = document.createElement('li'); li.textContent = text; return li;
                }));
                warnings.hidden = s.warnings.length === 0;
                document.querySelectorAll('input[name="suggestionToken"]').forEach(input => { input.value = result.suggestionToken; });
                status.textContent = result.message;
                complete = true;
            } catch (error) {
                // A lost response may have changed the nonce server-side. Never replay the request.
                status.textContent = 'Chưa xác định được kết quả đổi món. Hãy tải lại trang trước khi đổi hoặc lưu tiếp.';
            } finally {
                if (complete) {
                    buttons.forEach(([button, disabled]) => { button.disabled = disabled; });
                    previewBusy = false;
                }
            }
        });
    });

    document.querySelectorAll('form[data-submit-once]').forEach(form => {
        let submitted = false;
        form.addEventListener('submit', event => {
            if (event.defaultPrevented) return;
            if (previewBusy) { event.preventDefault(); return; }
            if (submitted) { event.preventDefault(); return; }
            submitted = true;
            form.querySelectorAll('button[type="submit"]').forEach(button => { button.disabled = true; });
        });
    });
})();
