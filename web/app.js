const SORT_BY = document.getElementById('sortBy');
const SORT_ORDER = document.getElementById('sortOrder');
const APPLY_SORT = document.getElementById('applySort');
const STATUS = document.getElementById('status');
const CONFERENCE_LIST = document.getElementById('conferenceList');
const RANK_FILTERS = document.getElementById('rankFilters');

let conferences = [];
const STALE_DEADLINE_DAYS = 14;

function resolveDeadlineTemplate(deadlineValue, year) {
  const text = String(deadlineValue || '').trim();
  if (!text) {
    return '';
  }

  if (!text.includes('%Y') && !text.includes('%y')) {
    return text;
  }

  const numericYear = Number(year);
  if (!Number.isFinite(numericYear)) {
    return text;
  }

  const yearString = String(numericYear);
  return text.replace(/%Y/g, yearString).replace(/%y/g, yearString);
}

function isKnownTimezone(timezone) {
  if (!timezone) {
    return false;
  }

  const value = String(timezone).trim().toLowerCase();
  return !['unknown', 'n/a', 'na', 'tbd', 'none', 'null', ''].includes(value);
}

function normalizeTimezoneCandidates(timezone) {
  const raw = String(timezone).trim();
  const candidates = [raw];

  const upper = raw.toUpperCase();
  const utcOffset = upper.match(/^(UTC|GMT)([+-]\d{1,2})$/);
  if (utcOffset) {
    candidates.push(`UTC${utcOffset[2]}`);
  }

  if (raw.includes('/')) {
    const titleCase = raw
      .split('/')
      .map((part) => part.toLowerCase().replace(/(^|[_-])(\w)/g, (m, sep, ch) => `${sep}${ch.toUpperCase()}`))
      .join('/');
    candidates.push(titleCase);
  }

  return [...new Set(candidates)];
}

function firstConcreteDeadline(conference) {
  const raw = conference.deadline;
  const values = Array.isArray(raw) ? raw : raw ? [raw] : [];

  for (const value of values) {
    const text = resolveDeadlineTemplate(value, conference.year);
    if (!text) {
      continue;
    }
    return text;
  }

  return null;
}

function getResolvedDeadlines(conference) {
  const raw = conference.deadline;
  const values = Array.isArray(raw) ? raw : raw ? [raw] : [];
  return values
    .map((value) => resolveDeadlineTemplate(value, conference.year))
    .filter((value) => Boolean(value));
}

function parseDeadlineInTimezone(deadlineText, timezone) {
  const candidates = normalizeTimezoneCandidates(timezone);
  const formats = [
    "yyyy-MM-dd HH:mm:ss",
    "yyyy-M-d HH:mm:ss",
    "yyyy-MM-dd HH:mm",
    "yyyy-M-d HH:mm",
    "yyyy/MM/dd HH:mm:ss",
    "yyyy/M/d HH:mm:ss",
    "yyyy/MM/dd HH:mm",
    "yyyy/M/d HH:mm",
  ];

  for (const zone of candidates) {
    let parsed = window.luxon.DateTime.fromISO(deadlineText, { zone });
    if (parsed.isValid) {
      return parsed;
    }

    for (const format of formats) {
      parsed = window.luxon.DateTime.fromFormat(deadlineText, format, { zone });
      if (parsed.isValid) {
        return parsed;
      }
    }
  }

  return null;
}

function sydneyDeadlineNote(conference) {
  if (!isKnownTimezone(conference.timezone)) {
    return null;
  }

  const deadlineText = firstUpcomingDeadline(conference, Date.now()) || firstConcreteDeadline(conference);
  if (!deadlineText) {
    return null;
  }

  const parsed = parseDeadlineInTimezone(deadlineText, conference.timezone);
  if (!parsed) {
    return `Sydney time conversion unavailable for timezone ${conference.timezone}.`;
  }

  const sydney = parsed.setZone('Australia/Sydney');
  if (!sydney.isValid) {
    return null;
  }

  return `Sydney time: ${sydney.toFormat('dd LLL yyyy, HH:mm')} (from ${conference.timezone}).`;
}

function rankPriority(rank) {
  const normalized = String(rank || '').trim().toUpperCase();
  const priorities = {
    'TOP4': 0,
    'A*': 1,
    'A': 2,
    'B': 3,
    'C': 4,
    'NOT RANKED': 8,
  };

  return priorities[normalized] ?? 7;
}

function rankLabel(rank) {
  const value = String(rank || '').trim();
  return value || 'N/A';
}

function getSelectedRanks() {
  const selected = new Set();
  const checkboxes = RANK_FILTERS.querySelectorAll('input[type="checkbox"]');
  for (const checkbox of checkboxes) {
    if (checkbox.checked) {
      selected.add(checkbox.value);
    }
  }
  return selected;
}

function setupRankFilters() {
  if (!RANK_FILTERS) {
    return;
  }

  RANK_FILTERS.innerHTML = '';

  const uniqueRanks = [...new Set(conferences.map((conference) => rankLabel(conference.rank)))].sort((a, b) => {
    const diff = rankPriority(a) - rankPriority(b);
    return diff !== 0 ? diff : a.localeCompare(b);
  });

  for (const rank of uniqueRanks) {
    const label = document.createElement('label');
    label.className = 'rank-option';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = rank;
    checkbox.checked = true;
    checkbox.addEventListener('change', applySortAndRender);

    const text = document.createElement('span');
    text.textContent = rank;

    label.appendChild(checkbox);
    label.appendChild(text);
    RANK_FILTERS.appendChild(label);
  }
}

function firstDeadlineTimestamp(conference) {
  const raw = conference.deadline;
  const values = Array.isArray(raw) ? raw : raw ? [raw] : [];

  let earliest = Number.POSITIVE_INFINITY;

  for (const value of values) {
    const text = resolveDeadlineTemplate(value, conference.year);
    if (!text) {
      continue;
    }

    const normalized = text.replace(' ', 'T');
    const timestamp = Date.parse(normalized);
    if (Number.isFinite(timestamp) && timestamp < earliest) {
      earliest = timestamp;
    }
  }

  return earliest;
}

function nearestRelevantDeadlineTimestamp(conference, nowMs) {
  const cutoff = nowMs - STALE_DEADLINE_DAYS * 24 * 60 * 60 * 1000;
  const timestamps = getResolvedDeadlines(conference)
    .map((value) => parseDeadlineTimestamp(value, conference.timezone))
    .filter((value) => Number.isFinite(value))
    .filter((value) => value >= cutoff)
    .sort((a, b) => a - b);

  if (!timestamps.length) {
    return Number.POSITIVE_INFINITY;
  }

  return timestamps[0];
}

function parseDeadlineTimestamp(deadlineText, timezone) {
  const text = String(deadlineText || '').trim();
  if (!text) {
    return null;
  }

  if (isKnownTimezone(timezone)) {
    const parsed = parseDeadlineInTimezone(text, timezone);
    if (parsed && parsed.isValid) {
      return parsed.toMillis();
    }
  }

  const normalized = text.replace(' ', 'T');
  const timestamp = Date.parse(normalized);
  return Number.isFinite(timestamp) ? timestamp : null;
}

function getDisplayDeadlines(conference, nowMs, sortOrder = 'asc') {
  const resolved = getResolvedDeadlines(conference);
  const visible = [];

  for (const text of resolved) {
    const timestamp = parseDeadlineTimestamp(text, conference.timezone);
    // Keep unknown-format deadlines visible; hide only known passed timestamps.
    if (!Number.isFinite(timestamp) || timestamp >= nowMs) {
      visible.push({ text, timestamp });
    }
  }

  const direction = sortOrder === 'desc' ? -1 : 1;
  visible.sort((left, right) => {
    const leftMissing = !Number.isFinite(left.timestamp);
    const rightMissing = !Number.isFinite(right.timestamp);

    if (leftMissing && !rightMissing) {
      return 1;
    }

    if (!leftMissing && rightMissing) {
      return -1;
    }

    if (left.timestamp !== right.timestamp) {
      return (left.timestamp - right.timestamp) * direction;
    }

    return left.text.localeCompare(right.text);
  });

  return visible.map((item) => item.text);
}

function firstUpcomingDeadline(conference, nowMs) {
  const resolved = getResolvedDeadlines(conference);
  const upcoming = [];

  for (const text of resolved) {
    const timestamp = parseDeadlineTimestamp(text, conference.timezone);
    if (!Number.isFinite(timestamp)) {
      continue;
    }
    if (timestamp >= nowMs) {
      upcoming.push({ text, timestamp });
    }
  }

  if (!upcoming.length) {
    return null;
  }

  upcoming.sort((a, b) => a.timestamp - b.timestamp);
  return upcoming[0].text;
}

function shouldDisplayConference(conference, nowMs) {
  const raw = conference.deadline;
  const values = Array.isArray(raw) ? raw : raw ? [raw] : [];

  if (!values.length) {
    return true;
  }

  const parsedTimestamps = values
    .map((value) => resolveDeadlineTemplate(value, conference.year))
    .map((value) => parseDeadlineTimestamp(value, conference.timezone))
    .filter((value) => Number.isFinite(value));

  if (!parsedTimestamps.length) {
    return true;
  }

  const cutoff = nowMs - STALE_DEADLINE_DAYS * 24 * 60 * 60 * 1000;
  const latestDeadline = Math.max(...parsedTimestamps);
  return latestDeadline >= cutoff;
}

function hasRecentlyPassedFinalDeadline(conference, nowMs) {
  const cutoff = nowMs - STALE_DEADLINE_DAYS * 24 * 60 * 60 * 1000;
  const parsedTimestamps = getResolvedDeadlines(conference)
    .map((value) => parseDeadlineTimestamp(value, conference.timezone))
    .filter((value) => Number.isFinite(value));

  if (!parsedTimestamps.length) {
    return false;
  }

  const finalDeadline = Math.max(...parsedTimestamps);
  return finalDeadline < nowMs && finalDeadline >= cutoff;
}

function hasNoVisibleDeadlines(conference, nowMs) {
  return getDisplayDeadlines(conference, nowMs).length === 0;
}

function hasFinalDeadlinePassedToday(conference, nowMs) {
  const parsedTimestamps = getResolvedDeadlines(conference)
    .map((value) => parseDeadlineTimestamp(value, conference.timezone))
    .filter((value) => Number.isFinite(value));

  if (!parsedTimestamps.length) {
    return false;
  }

  const finalDeadline = Math.max(...parsedTimestamps);
  if (finalDeadline >= nowMs) {
    return false;
  }

  const finalDate = new Date(finalDeadline);
  const nowDate = new Date(nowMs);

  return finalDate.getFullYear() === nowDate.getFullYear()
    && finalDate.getMonth() === nowDate.getMonth()
    && finalDate.getDate() === nowDate.getDate();
}

function compareConferences(a, b, sortBy, sortOrder, nowMs) {
  const direction = sortOrder === 'desc' ? -1 : 1;

  if (sortBy === 'name') {
    const left = String(a.name || '').toLowerCase();
    const right = String(b.name || '').toLowerCase();
    const result = left.localeCompare(right);
    if (result !== 0) {
      return result * direction;
    }
  }

  if (sortBy === 'year') {
    const left = Number(a.year) || 0;
    const right = Number(b.year) || 0;
    if (left !== right) {
      return (left - right) * direction;
    }
  }

  if (sortBy === 'rank') {
    const left = rankPriority(a.rank);
    const right = rankPriority(b.rank);
    if (left !== right) {
      return (left - right) * direction;
    }
  }

  if (sortBy === 'deadline') {
    const leftVisibleDeadlines = getDisplayDeadlines(a, nowMs, sortOrder);
    const rightVisibleDeadlines = getDisplayDeadlines(b, nowMs, sortOrder);
    const leftIsNA = leftVisibleDeadlines.length === 0;
    const rightIsNA = rightVisibleDeadlines.length === 0;

    if (leftIsNA && !rightIsNA) {
      return 1;
    }

    if (!leftIsNA && rightIsNA) {
      return -1;
    }

    const left = nearestRelevantDeadlineTimestamp(a, nowMs);
    const right = nearestRelevantDeadlineTimestamp(b, nowMs);
    const leftMissing = !Number.isFinite(left);
    const rightMissing = !Number.isFinite(right);

    if (leftMissing && !rightMissing) {
      return 1;
    }

    if (!leftMissing && rightMissing) {
      return -1;
    }

    if (left !== right) {
      return (left - right) * direction;
    }
  }

  const leftName = String(a.name || '').toLowerCase();
  const rightName = String(b.name || '').toLowerCase();
  return leftName.localeCompare(rightName);
}

function renderConferenceCards(items) {
  CONFERENCE_LIST.innerHTML = '';

  if (!items.length) {
    CONFERENCE_LIST.innerHTML = '<div class="empty">No conferences found in YAML.</div>';
    return;
  }

  const fragment = document.createDocumentFragment();
  const nowMs = Date.now();
  const deadlineSortOrder = SORT_ORDER?.value || 'asc';

  for (const conference of items) {
    const card = document.createElement('article');
    card.className = 'card';

    if (hasNoVisibleDeadlines(conference, nowMs)) {
      card.classList.add('card-no-deadline');
    } else if (hasFinalDeadlinePassedToday(conference, nowMs)) {
      card.classList.add('card-passed-today');
    } else if (hasRecentlyPassedFinalDeadline(conference, nowMs)) {
      card.classList.add('card-recently-closed');
    }

    const name = document.createElement('h2');
    name.textContent = conference.name || 'Unnamed conference';

    const meta = document.createElement('div');
    meta.className = 'card-meta';

    const yearTag = document.createElement('span');
    yearTag.className = 'tag';
    yearTag.textContent = `Year: ${conference.year || 'N/A'}`;

    const rankTag = document.createElement('span');
    rankTag.className = 'tag';
    rankTag.textContent = `Rank: ${conference.rank || 'N/A'}`;

    meta.appendChild(yearTag);
    meta.appendChild(rankTag);

    card.appendChild(name);
    card.appendChild(meta);

    const deadlineBlock = document.createElement('div');
    deadlineBlock.className = 'deadline-block';

    const deadlineLabel = document.createElement('p');
    deadlineLabel.className = 'deadline-label';
    deadlineLabel.textContent = 'Deadlines';
    deadlineBlock.appendChild(deadlineLabel);

    const deadlineList = document.createElement('ul');
    deadlineList.className = 'deadline-list';
    const visibleDeadlines = getDisplayDeadlines(conference, nowMs, deadlineSortOrder);

    if (visibleDeadlines.length) {
      for (const deadline of visibleDeadlines) {
        const item = document.createElement('li');
        item.textContent = deadline;
        deadlineList.appendChild(item);
      }
    } else {
      const item = document.createElement('li');
      item.textContent = 'N/A';
      deadlineList.appendChild(item);
    }

    deadlineBlock.appendChild(deadlineList);
    card.appendChild(deadlineBlock);

    const description = document.createElement('p');
    description.className = 'conference-description';
    description.textContent = conference.description || 'No description available.';
    card.appendChild(description);

    const place = document.createElement('p');
    place.className = 'conference-place';
    place.textContent = `Place: ${conference.place || 'N/A'}`;
    card.appendChild(place);

    if (conference.link) {
      const link = document.createElement('a');
      link.className = 'conference-link';
      link.href = String(conference.link);
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = 'Conference website';
      card.appendChild(link);
    }

    const timezoneNote = sydneyDeadlineNote(conference);
    if (timezoneNote) {
      const note = document.createElement('p');
      note.className = 'timezone-note';
      note.textContent = timezoneNote;
      card.appendChild(note);
    }

    fragment.appendChild(card);
  }

  CONFERENCE_LIST.appendChild(fragment);
}

function applySortAndRender() {
  const sortBy = SORT_BY.value;
  const sortOrder = SORT_ORDER.value;
  const nowMs = Date.now();
  const selectedRanks = getSelectedRanks();

  const visible = conferences
    .filter((conference) => selectedRanks.has(rankLabel(conference.rank)))
    .filter((conference) => shouldDisplayConference(conference, nowMs));

  const sorted = [...visible].sort((a, b) => compareConferences(a, b, sortBy, sortOrder, nowMs));
  renderConferenceCards(sorted);
  const hiddenCount = conferences.length - sorted.length;
  STATUS.textContent = `Showing ${sorted.length} conferences sorted by ${sortBy} (${sortOrder}). Hidden ${hiddenCount} past-deadline items (> ${STALE_DEADLINE_DAYS} days).`;
}

async function loadConferences() {
  try {
    const response = await fetch('../resources/combined_conferences.yaml', { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`Unable to load YAML (HTTP ${response.status}).`);
    }

    const yamlText = await response.text();
    const parsed = window.jsyaml.load(yamlText);

    if (!Array.isArray(parsed)) {
      throw new Error('YAML root should be a list of conferences.');
    }

    conferences = parsed.filter((item) => item && typeof item === 'object');
    setupRankFilters();
    applySortAndRender();
  } catch (error) {
    STATUS.textContent = `Failed to load conferences: ${error.message}`;
    CONFERENCE_LIST.innerHTML = '<div class="empty">Start a local server at repository root (for example: python3 -m http.server 8000), then open /web/.</div>';
  }
}

APPLY_SORT.addEventListener('click', applySortAndRender);
SORT_BY.addEventListener('change', applySortAndRender);
SORT_ORDER.addEventListener('change', applySortAndRender);

loadConferences();
