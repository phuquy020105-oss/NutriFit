document.addEventListener('DOMContentLoaded', () => {
  const categories = document.getElementById('nf-category-panel');
  const workouts = document.getElementById('nf-workout-panel');
  const heading = document.getElementById('nf-selected-category');
  const search = document.getElementById('nf-workout-search');
  const cards = [...document.querySelectorAll('.nf-workout-card')];
  const empty = document.getElementById('nf-filter-empty');
  if (!categories || !workouts || !heading || !search || !empty) return;
  let selected = '';
  function refresh() {
    const term = search.value.trim().toLocaleLowerCase('vi');
    let count = 0;
    cards.forEach(card => {
      const match = card.dataset.category === selected && card.dataset.search.includes(term);
      card.hidden = !match;
      if (match) count++;
    });
    empty.hidden = count > 0;
  }
  document.querySelectorAll('[data-open-category]').forEach(button => {
    button.addEventListener('click', () => {
      selected = button.dataset.openCategory;
      heading.textContent = button.dataset.categoryName;
      categories.hidden = true;
      workouts.hidden = false;
      search.value = '';
      refresh();
    });
  });
  document.getElementById('nf-back-categories')?.addEventListener('click', () => {
    workouts.hidden = true;
    categories.hidden = false;
    selected = '';
  });
  search.addEventListener('input', refresh);
});
