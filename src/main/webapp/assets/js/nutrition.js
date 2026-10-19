(() => {
    'use strict';

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

    const suggestionForm = document.querySelector('[data-suggestion-form]');
    if (suggestionForm) {
        const status = suggestionForm.querySelector('[data-suggestion-status]');
        const save = suggestionForm.querySelector('[data-save-suggestion]');
        const inputs = [...suggestionForm.querySelectorAll('[data-suggestion-servings]')];
        let revision = 0;
        let timer;
        const recalculate = async () => {
            const current = ++revision;
            save.disabled = true;
            if (!inputs.every(input => input.checkValidity())) {
                status.textContent = 'Khẩu phần phải dương, tối đa hai chữ số thập phân và trong giới hạn cho phép.';
                return;
            }
            status.textContent = 'Đang tính lại dinh dưỡng…';
            const body = new FormData(suggestionForm);
            body.set('action', 'preview');
            try {
                const response = await fetch(suggestionForm.action, {
                    method: 'POST', body, credentials: 'same-origin',
                    headers: { 'Accept': 'application/json' }
                });
                if (!response.ok) throw new Error('Preview rejected');
                const data = await response.json();
                if (current !== revision) return;
                for (const meal of data.meals) {
                    const card = suggestionForm.querySelector('[data-suggestion-meal="' + meal.mealType + '"]');
                    for (const [key, value] of Object.entries(meal.nutrition)) {
                        card.querySelector('[data-fact="' + key + '"]').textContent = value;
                    }
                }
                for (const [key, value] of Object.entries(data.total)) {
                    suggestionForm.querySelector('[data-total-fact="' + key + '"]').textContent = value;
                }
                suggestionForm.querySelector('[data-suggestion-target]').textContent = data.targetKcal;
                suggestionForm.querySelector('[data-suggestion-difference]').textContent = data.differenceKcal;
                document.querySelector('[data-suggestion-mode]').textContent = data.personalized
                    ? 'Đang áp dụng sở thích Premium: loại DISLIKE và ưu tiên LIKE.'
                    : 'Gợi ý Free theo mục tiêu calories, không áp dụng LIKE/DISLIKE.';
                status.textContent = 'Đã tính lại trên server. Chưa lưu vào nhật ký.';
                save.disabled = false;
            } catch (error) {
                if (current !== revision) return;
                status.textContent = 'Chưa thể tính lại. Gợi ý có thể đã hết hạn hoặc món không còn phù hợp; hãy tải lại trang để kiểm tra.';
            }
        };
        inputs.forEach(input => input.addEventListener('input', () => {
            revision++;
            clearTimeout(timer);
            save.disabled = true;
            timer = setTimeout(recalculate, 250);
        }));
        suggestionForm.querySelector('[data-refresh-suggestion]').addEventListener('click', () => {
            clearTimeout(timer);
            recalculate();
        });
        suggestionForm.addEventListener('submit', event => {
            if (save.disabled) { event.preventDefault(); return; }
            save.disabled = true;
            status.textContent = 'Đang lưu thực đơn…';
        });
    }
})();
