// Recording-only accessibility aid. It follows real pointer input, never graph data.
// Installed transiently through the local tab's CDP; reload removes it completely.
(() => {
  if (document.getElementById('demo-live-pointer')) throw Error('Pointer already installed');
  const style = document.createElement('style');
  style.id = 'demo-live-pointer-style';
  style.textContent = `
    #demo-live-pointer { position:fixed; left:0; top:0; width:36px; height:44px;
      z-index:2147483647; pointer-events:none; transform:translate(-100px,-100px);
      filter:drop-shadow(0 2px 3px #000a); }
    .demo-live-click { position:fixed; width:46px; height:46px; margin:-23px;
      border:3px solid #91edc4; border-radius:50%; z-index:2147483646;
      pointer-events:none; animation:demo-live-ring .65s ease-out forwards; }
    @keyframes demo-live-ring { from { transform:scale(.45); opacity:1; }
      to { transform:scale(1.7); opacity:0; } }
  `;
  document.head.append(style);
  const pointer = document.createElement('div');
  pointer.id = 'demo-live-pointer';
  pointer.setAttribute('aria-hidden', 'true');
  pointer.innerHTML = '<svg width="36" height="44" viewBox="0 0 36 44"><path d="M3 2 L3 32 L11 25 L18 40 L25 37 L18 23 L30 23 Z" fill="#ffffff" stroke="#132d27" stroke-width="2.3" stroke-linejoin="round"/></svg>';
  document.body.append(pointer);
  const move = e => { pointer.style.transform = `translate(${e.clientX - 3}px,${e.clientY - 2}px)`; };
  document.addEventListener('pointermove', move, {capture:true});
  document.addEventListener('pointerdown', e => {
    move(e);
    const ring = document.createElement('div');
    ring.className = 'demo-live-click';
    ring.style.left = `${e.clientX}px`; ring.style.top = `${e.clientY}px`;
    ring.setAttribute('aria-hidden', 'true');
    document.body.append(ring);
    ring.addEventListener('animationend', () => ring.remove(), {once:true});
  }, {capture:true});
  return 'Live pointer overlay installed; no application data or behavior changed.';
})();
