/**
 * MultiCardz™ Application Logic
 * UI controls, card/tag creation, and event handlers
 * Follows web performance best practices
 */

// Zone drop handler
function handleZoneDrop(event, container) {
  if (event.dataTransfer.types.includes('text/zone')) {
    event.preventDefault();
    container.classList.remove('zone-drag-over');

    const zoneType = event.dataTransfer.getData('text/zone');
    let draggedZone;

    if (zoneType === 'filter') {
      draggedZone = document.querySelector('.filter-zone-container[data-zone-type="filter"]');
    } else {
      draggedZone = document.querySelector('.' + zoneType + '-zone');
    }

    if (draggedZone && !container.contains(draggedZone)) {
      container.appendChild(draggedZone);
    }
  }
}

// Toggle grid row visibility
function toggleRow(rowNum) {
  const grid = document.getElementById('spatialGrid');
  const rowElements = document.querySelectorAll('.row-' + rowNum);
  const toggles = document.querySelectorAll('.collapse-row' + rowNum);

  rowElements.forEach(elem => elem.classList.toggle('collapsed'));

  const isCollapsed = rowElements[0]?.classList.contains('collapsed');
  const action = isCollapsed ? 'add' : 'remove';

  grid.classList[action]('row-' + rowNum + '-collapsed');
  toggles.forEach(toggle => toggle.classList[action]('is-collapsed'));
}

// Toggle grid column visibility
function toggleColumn(colNum) {
  const grid = document.getElementById('spatialGrid');
  const colElements = document.querySelectorAll('.col-' + colNum);
  const toggle = document.querySelector('.collapse-col' + colNum);

  colElements.forEach(elem => elem.classList.toggle('collapsed'));

  const isCollapsed = colElements[0]?.classList.contains('collapsed');
  const action = isCollapsed ? 'add' : 'remove';

  grid.classList[action]('col-' + colNum + '-collapsed');
  toggle?.classList[action]('is-collapsed');
}

// Toggle section (universal/ui controls)
function toggleSection(section) {
  const sectionElement = document.querySelector(`.${section}-control`);
  const toggleButton = document.querySelector(`.collapse-${section}`);

  if (sectionElement && toggleButton) {
    sectionElement.classList.toggle('collapsed-section');
    const chevron = toggleButton.querySelector('.chevron path');
    const isCollapsed = sectionElement.classList.contains('collapsed-section');

    toggleButton.classList.toggle('is-collapsed', isCollapsed);
    chevron?.setAttribute('d', isCollapsed ? 'M4 10L8 6L12 10' : 'M4 6L8 10L12 6');
  }
}

// Switch lesson
async function switchLesson(lessonValue) {
  try {
    const response = await fetch('/api/v2/lessons/switch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lessonId: lessonValue })
    });

    const data = await response.json();

    if (data.status === 'success') {
      localStorage.setItem('currentLesson', lessonValue);
      window.currentLessonState = data.lesson_state;

      if (window.dragDropSystem) {
        window.dragDropSystem.clearAllZones();
      }

      const currentUrl = new URL(window.location.href);
      currentUrl.searchParams.set('lesson', lessonValue);
      window.location.href = currentUrl.toString();
    } else {
      console.error('Failed to switch lesson:', data);
    }
  } catch (error) {
    console.error('Error switching lesson:', error);
  }
}

// Placeholder for database switching
function switchDatabase(databaseValue) {
  // TODO: Implement database switching logic
}

// Create tag (delegates to drag-drop system)
async function createTag(tagName, cloudType = 'user') {
  if (window.dragDropSystem) {
    return await window.dragDropSystem.createTag(tagName, cloudType);
  }
}

// Create new card with tags from zones
async function createNewCard() {
  const unionTags = Array.from(document.querySelectorAll('[data-zone-type="union"] .tag'));
  const intersectionTags = Array.from(document.querySelectorAll('[data-zone-type="intersection"] .tag'));
  const allTags = [...new Set([...unionTags, ...intersectionTags])];

  const tagIds = allTags.map(t => t.getAttribute('data-tag-id')).filter(Boolean);
  const tagNames = allTags.map(t => t.getAttribute('data-tag')).filter(Boolean);
  const cardId = crypto.randomUUID();

  const cardContainer = document.querySelector('.card-container');
  const cardElement = document.createElement('div');
  cardElement.className = 'card-item';
  cardElement.setAttribute('data-card-id', cardId);

  cardElement.innerHTML = `
    <div class="card-content">
      <button class="card-delete" title="Delete card">×</button>
      <div class="card-header">
        <h4 class="card-title" contenteditable="true" style="outline: 2px solid #3b82f6;"></h4>
      </div>
      <div class="card-footer">
        <div class="card-tags-section">
          <div class="card-tags-header">
            <span class="card-tags-label">tags (${tagNames.length})</span>
          </div>
          <div class="card-tags" style="display: block;">
            ${tagNames.map((name, i) =>
              `<span class="card-tag" data-tag="${name}" data-tag-id="${tagIds[i]}">${name} <span class="tag-remove">×</span></span>`
            ).join('')}
          </div>
        </div>
      </div>
    </div>
  `;

  cardContainer.appendChild(cardElement);

  try {
    const response = await fetch('/api/v2/cards/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Untitled', tag_ids: tagIds })
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('Failed to create card:', error);
      alert('Failed to create card: ' + (error.message || 'Unknown error'));
      cardElement.remove();
      return;
    }

    // Update tag counts for tags in zones
    const tagsInPlayElement = document.getElementById('tagsInPlay');
    if (tagsInPlayElement) {
      try {
        const tagsInPlay = JSON.parse(tagsInPlayElement.value);
        const tagsToUpdate = new Set([
          ...(tagsInPlay.union || []),
          ...(tagsInPlay.intersection || [])
        ]);

        // Tag counts will be updated automatically via polling service
      } catch (e) {
        console.error('Failed to update tag counts:', e);
      }
    }
  } catch (error) {
    console.error('Failed to create card:', error);
    alert('Failed to create card');
    cardElement.remove();
    return;
  }

  // Setup title editing
  const titleElement = cardElement.querySelector('.card-title');
  titleElement.focus();

  let titleSaved = false;
  const saveTitle = async () => {
    if (titleSaved) return;

    const name = titleElement.textContent.trim();
    if (!name) {
      titleElement.textContent = 'Untitled';
      return;
    }

    titleSaved = true;
    titleElement.setAttribute('contenteditable', 'false');
    titleElement.style.outline = 'none';

    try {
      const response = await fetch('/api/v2/cards/update-title', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_id: cardId, title: name })
      });

      if (!response.ok) {
        const error = await response.json();
        console.error('Failed to update title:', error);
        titleSaved = false;
      }
    } catch (error) {
      console.error('Failed to update title:', error);
      titleSaved = false;
    }
  };

  titleElement.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      saveTitle();
      titleElement.blur();
    }
  });

  titleElement.addEventListener('blur', saveTitle);
}

// Make card title editable (legacy function - keeping for compatibility)
function makeCardTitleEditable(cardElement) {
  const titleElement = cardElement.querySelector('.card-title');
  if (!titleElement || titleElement.querySelector('input')) return;

  const currentTitle = titleElement.textContent;
  const input = document.createElement('input');
  input.type = 'text';
  input.value = currentTitle;
  input.className = 'card-title-input';
  Object.assign(input.style, {
    width: '100%',
    font: 'inherit',
    border: '1px solid #ccc',
    padding: '2px'
  });

  titleElement.textContent = '';
  titleElement.appendChild(input);
  input.focus();
  input.select();

  const saveTitle = async () => {
    const newTitle = input.value.trim();
    if (newTitle && newTitle !== currentTitle) {
      const cardId = cardElement.getAttribute('data-card-id');
      try {
        const response = await fetch('/api/v2/cards/update-title', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ card_id: cardId, title: newTitle })
        });
        titleElement.textContent = response.ok ? newTitle : currentTitle;
      } catch (error) {
        console.error('Failed to update card title:', error);
        titleElement.textContent = currentTitle;
      }
    } else {
      titleElement.textContent = currentTitle;
    }
  };

  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      saveTitle();
    }
  });

  input.addEventListener('blur', saveTitle);
}

// Initialize app when DOM is ready
function initializeApp() {
  // Setup tag input handlers
  document.querySelectorAll('.tag-input').forEach(input => {
    input.addEventListener('keypress', async function(e) {
      if (e.key === 'Enter' && this.value.trim()) {
        const tagName = this.value.trim();
        const cloudType = this.closest('.cloud-user') ? 'user' :
                         this.closest('.cloud-ai') ? 'ai' : 'user';
        await createTag(tagName, cloudType);
        this.value = '';
      }
    });
  });

  // Setup card title editing
  document.addEventListener('click', (e) => {
    if (e.target.closest('.card-title') && !e.target.closest('input')) {
      const card = e.target.closest('.card-item');
      if (card) makeCardTitleEditable(card);
    }
  });

  // Keyboard shortcut for title editing
  document.addEventListener('keypress', (e) => {
    if (e.key === 't' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
      const hoveredCard = document.elementFromPoint(e.clientX || 0, e.clientY || 0)?.closest('.card-item');
      if (hoveredCard) {
        e.preventDefault();
        makeCardTitleEditable(hoveredCard);
      }
    }
  });

  // Card tag drop handling
  window.addEventListener('cardTagDrop', async (e) => {
    const { cardId, tagId, tagName, cardTags } = e.detail;

    if (cardTags.querySelector(`[data-tag="${tagName}"]`)) {
      return;
    }

    try {
      const response = await fetch('/api/v2/cards/add-tag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_id: cardId, tag_id: tagId })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        const tagRep = document.createElement('span');
        tagRep.className = 'card-tag';
        tagRep.setAttribute('data-tag', tagName);
        tagRep.setAttribute('data-tag-id', tagId);
        tagRep.innerHTML = `${tagName} <span class="tag-remove">×</span>`;
        cardTags.appendChild(tagRep);
      } else {
        console.error('API returned error:', result);
      }
    } catch (error) {
      console.error('Failed to add tag to card:', error);
    }
  });

  // Wait for drag-drop system with exponential backoff
  const initDragDrop = (attempt = 0) => {
    if (window.dragDropSystem) {
      window.dragDropSystem.updateStateAndRender();
    } else if (attempt < 3) {
      setTimeout(() => initDragDrop(attempt + 1), 500 * Math.pow(2, attempt));
    }
  };

  initDragDrop();

  // Register tag count update listener
  if (window.tagCountEmitter) {
    window.tagCountEmitter.on('tag-count-changed', ({ tagId, count }) => {
      // Find all tag elements with this tagId and update their count display
      const tagElements = document.querySelectorAll(`[data-tag-id="${tagId}"]`);

      tagElements.forEach(tagElement => {
        // Only update if it's a tag in the cloud (has the tag class, not card-tag)
        if (tagElement.classList.contains('tag')) {
          const tagName = tagElement.getAttribute('data-tag');
          if (tagName) {
            tagElement.innerHTML = `${tagName} (${count}) <button class="tag-delete" data-tag-id="${tagId}" title="Delete tag">×</button>`;
          }
        }
      });
    });
  }
}

// Run when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
