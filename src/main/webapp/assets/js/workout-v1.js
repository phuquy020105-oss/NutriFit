document.addEventListener('DOMContentLoaded', () => {
    const search = document.getElementById('workoutSearch');
    const access = document.getElementById('accessFilter');
    const cards = Array.from(document.querySelectorAll('#workoutGrid .nf-card'));
    const empty = document.getElementById('filterEmpty');
    if (!search || !access || !cards.length) return;
    function filterCards() {
        const query = search.value.trim().toLocaleLowerCase('vi');
        const tier = access.value.toUpperCase();
        let visible = 0;
        for (const card of cards) {
            const matchesText = card.textContent.toLocaleLowerCase('vi').includes(query);
            const matchesTier = !tier || (card.dataset.access || '').toUpperCase() === tier;
            card.hidden = !(matchesText && matchesTier);
            if (!card.hidden) visible++;
        }
        if (empty) empty.hidden = visible !== 0;
    }
    search.addEventListener('input', filterCards);
    access.addEventListener('change', filterCards);
});
