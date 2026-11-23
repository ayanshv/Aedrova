# ruff: noqa: E501
"""Small scripts run inside the page, in an isolated world so the page cannot change them."""

READ = r"""
(() => {
  const visible = (e) => {
    const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
  };
  document.querySelectorAll('[data-aedrova-ref]').forEach((e) => e.removeAttribute('data-aedrova-ref'));
  const elements = [];
  const sel = 'a[href],button,input,textarea,select,[role=button],[role=link],[role=searchbox],[onclick]';
  for (const e of document.querySelectorAll(sel)) {
    if (elements.length >= 80 || !visible(e)) continue;
    const ref = elements.length + 1;
    e.setAttribute('data-aedrova-ref', String(ref));
    const type = (e.getAttribute('type') || e.tagName).toLowerCase();
    const label = (e.innerText || e.getAttribute('aria-label') || e.getAttribute('placeholder')
      || e.getAttribute('title') || '').trim().replace(/\s+/g, ' ').slice(0, 80);
    elements.push({ref, tag: e.tagName.toLowerCase(), type: type, text: type === 'password' ? '' : label});
  }
  return {
    title: document.title.slice(0, 200), url: location.href,
    text: (document.body ? document.body.innerText : '').slice(0, 15000), elements: elements,
  };
})()
"""

INSPECT = r"""
((ref) => {
  const e = document.querySelector('[data-aedrova-ref="' + ref + '"]');
  if (!e) return {error: 'That element is no longer on the page. Read the page again.'};
  const label = e.labels && e.labels[0] ? e.labels[0].innerText : '';
  return {
    tag: e.tagName.toLowerCase(), type: (e.getAttribute('type') || '').toLowerCase(),
    autocomplete: e.getAttribute('autocomplete') || '', name: e.getAttribute('name') || '',
    id: e.id || '', placeholder: e.getAttribute('placeholder') || '', label: label,
    aria: e.getAttribute('aria-label') || '',
    text: (e.innerText || e.value || '').trim().slice(0, 80), value: '',
    editable: ['input', 'textarea', 'select'].includes(e.tagName.toLowerCase()) || e.isContentEditable,
  };
})(%s)
"""

CLICK = r"""
((ref) => {
  const e = document.querySelector('[data-aedrova-ref="' + ref + '"]');
  if (!e) return {error: 'That element is no longer on the page. Read the page again.'};
  e.scrollIntoView({block: 'center', inline: 'center'});
  const r = e.getBoundingClientRect();
  e.click();
  return {x: r.left + r.width / 2, y: r.top + r.height / 2};
})(%s)
"""

TYPE = r"""
((ref, text, submit) => {
  const e = document.querySelector('[data-aedrova-ref="' + ref + '"]');
  if (!e) return {error: 'That element is no longer on the page. Read the page again.'};
  e.scrollIntoView({block: 'center'});
  e.focus();
  const proto = e.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, 'value');
  if (setter && setter.set) setter.set.call(e, text); else e.value = text;
  e.dispatchEvent(new Event('input', {bubbles: true}));
  e.dispatchEvent(new Event('change', {bubbles: true}));
  if (submit) {
    if (e.form && e.form.requestSubmit) e.form.requestSubmit();
    else e.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
  }
  const r = e.getBoundingClientRect();
  return {x: r.left + r.width / 2, y: r.top + r.height / 2};
})(%s, %s, %s)
"""

SCROLL = (
    "window.scrollBy(0, %d); ({y: Math.round(window.scrollY), max: document.body.scrollHeight})"
)
