// One floating tooltip shared by every chart on the page. Marks opt in with data-tip-value and
// data-tip-label, and respond to pointer and keyboard focus alike. Text is set with textContent.
let tip: HTMLDivElement | null = null;

function ensureTip(): HTMLDivElement {
	if (!tip) {
		tip = document.createElement('div');
		tip.className = 'ev-tip';
		tip.setAttribute('role', 'tooltip');
		document.body.appendChild(tip);
	}
	return tip;
}

function show(el: HTMLElement, x: number, y: number) {
	const t = ensureTip();
	t.replaceChildren();
	const v = document.createElement('strong');
	v.textContent = el.dataset.tipValue ?? '';
	const l = document.createElement('div');
	l.textContent = el.dataset.tipLabel ?? '';
	t.append(v, l);
	const w = t.offsetWidth;
	const left = Math.min(window.innerWidth - w - 8, Math.max(8, x - w / 2));
	t.style.left = `${left}px`;
	t.style.top = `${Math.max(8, y - t.offsetHeight - 12)}px`;
	t.classList.add('is-on');
}

function hide() {
	tip?.classList.remove('is-on');
}

export function bindTips(root: ParentNode = document) {
	root.querySelectorAll<HTMLElement>('[data-tip-value]').forEach((el) => {
		if (el.dataset.tipBound) return;
		el.dataset.tipBound = '1';
		el.addEventListener('pointermove', (e) => show(el, e.clientX, e.clientY));
		el.addEventListener('pointerleave', hide);
		el.addEventListener('focus', () => {
			const r = el.getBoundingClientRect();
			show(el, r.left + r.width / 2, r.top);
		});
		el.addEventListener('blur', hide);
	});
}
