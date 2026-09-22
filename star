<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 36" role="img" aria-label="Star us on GitHub — cursor clicks the star, it fills yellow, a small burst fires, count ticks up">
  <title>Star us on GitHub</title>
  <desc>Compact GitHub-style Star button that animates on a 4.5s loop: cursor glides in, clicks the outline star, the star fills yellow, a small confetti burst fires, and the count pill ticks up.</desc>
  <defs>
    <style>
      .empty { animation: emptyStar 4.5s ease-in-out infinite; }
      .full  { animation: fullStar  4.5s ease-in-out infinite;
               transform-origin: 14px 18px; transform-box: fill-box; opacity: 0; }
      @keyframes emptyStar { 0%,28%,82%,100% { opacity: 1 } 34%,78% { opacity: 0 } }
      @keyframes fullStar  { 0%,28%,82%,100% { opacity: 0; transform: scale(0.85); }
                              34% { opacity: 1; transform: scale(1.3); }
                              40%,78% { opacity: 1; transform: scale(1); } }

      .label-star, .count-10    { animation: labelOff 4.5s ease-in-out infinite; }
      .label-starred, .count-101 { animation: labelOn  4.5s ease-in-out infinite; opacity: 0; }
      @keyframes labelOff { 0%,28%,82%,100% { opacity: 1 } 34%,78% { opacity: 0 } }
      @keyframes labelOn  { 0%,28%,82%,100% { opacity: 0 } 34%,78% { opacity: 1 } }

      .ripple {
        opacity: 0;
        animation: ripple 4.5s ease-out infinite;
        transform-origin: 14px 18px;
        transform-box: fill-box;
      }
      @keyframes ripple {
        0%,28%,50%,100% { opacity: 0; transform: scale(0.4); }
        32% { opacity: 0.85; transform: scale(0.5); }
        44% { opacity: 0; transform: scale(2.4); }
      }

      [class^="bs"] {
        transform-box: fill-box; transform-origin: center; opacity: 0;
      }
      .bs1 { animation: bs1 4.5s ease-out infinite; }
      .bs2 { animation: bs2 4.5s ease-out infinite; }
      .bs3 { animation: bs3 4.5s ease-out infinite; }
      .bs4 { animation: bs4 4.5s ease-out infinite; }
      @keyframes bs1 { 0%,30%,50%,100% { opacity:0; transform: translate(0,0) scale(0) } 36% { opacity:1; transform: translate(0,0) scale(0.9) } 48% { opacity:0; transform: translate( 14px,-14px) scale(1.2) rotate(60deg) } }
      @keyframes bs2 { 0%,30%,50%,100% { opacity:0; transform: translate(0,0) scale(0) } 36% { opacity:1; transform: translate(0,0) scale(0.7) } 48% { opacity:0; transform: translate(  2px,-18px) scale(1.0) rotate(-60deg) } }
      @keyframes bs3 { 0%,30%,52%,100% { opacity:0; transform: translate(0,0) scale(0) } 37% { opacity:1; transform: translate(0,0) scale(0.8) } 50% { opacity:0; transform: translate(-14px,-10px) scale(1.1) rotate(80deg) } }
      @keyframes bs4 { 0%,30%,50%,100% { opacity:0; transform: translate(0,0) scale(0) } 37% { opacity:1; transform: translate(0,0) scale(0.6) } 48% { opacity:0; transform: translate(-10px, 12px) scale(0.9) rotate(-100deg) } }

      .cursor { animation: cursorMove 4.5s ease-in-out infinite; }
      @keyframes cursorMove {
        0%   { transform: translate(100px, 34px) rotate(-20deg); }
        22%  { transform: translate(14px,  20px) rotate(0deg);   }
        30%  { transform: translate(14px,  20px) rotate(0deg) scale(0.82); }
        36%  { transform: translate(14px,  20px) rotate(0deg) scale(1); }
        78%  { transform: translate(14px,  20px) rotate(0deg); }
        100% { transform: translate(100px, 34px) rotate(-20deg); }
      }
    </style>
    <path id="ts" d="M 0 -3 L 0.9 -0.9 L 3 -0.85 L 1.3 0.55 L 1.85 2.65 L 0 1.5 L -1.85 2.65 L -1.3 0.55 L -3 -0.85 L -0.9 -0.9 Z"/>
  </defs>

  <!-- pill shell -->
  <rect x="0.5" y="4" width="127" height="28" rx="8" fill="rgba(252,243,216,0.05)" stroke="rgba(252,243,216,0.35)" stroke-width="1"/>

  <!-- star icons (centered 14, 18) -->
  <path class="empty" d="M14 11 L15.5 14.5 L19 14.7 L16 17 L16.9 20.6 L14 18.7 L11.1 20.6 L12 17 L9 14.7 L12.5 14.5 Z" fill="none" stroke="#FFD94A" stroke-width="1.4" stroke-linejoin="round"/>
  <path class="full" d="M14 11 L15.5 14.5 L19 14.7 L16 17 L16.9 20.6 L14 18.7 L11.1 20.6 L12 17 L9 14.7 L12.5 14.5 Z" fill="#FFD94A" stroke="#FFD94A" stroke-width="1.4" stroke-linejoin="round"/>

  <!-- ripple rings -->
  <circle class="ripple" cx="14" cy="18" r="5" fill="none" stroke="#FFD94A" stroke-width="1"/>
  <circle class="ripple" cx="14" cy="18" r="5" fill="none" stroke="#FFD94A" stroke-width="1" style="animation-delay:0.08s"/>

  <!-- confetti burst -->
  <g transform="translate(14,18)">
    <use class="bs1" href="#ts" fill="#FFD94A"/>
    <use class="bs2" href="#ts" fill="#F5B07F"/>
    <use class="bs3" href="#ts" fill="#FFE787"/>
    <use class="bs4" href="#ts" fill="#FFD94A"/>
  </g>

  <!-- divider -->
  <line x1="26" y1="10" x2="26" y2="26" stroke="rgba(252,243,216,0.22)"/>

  <!-- Star / Starred label -->
  <g font-family="Inter, -apple-system, system-ui, sans-serif" font-size="12" font-weight="600" fill="#FCF3D8">
    <text class="label-star" x="34" y="23">Star</text>
    <text class="label-starred" x="34" y="23">Starred</text>
  </g>

  <!-- count pill -->
  <g>
    <rect x="84" y="10" width="36" height="16" rx="4" fill="rgba(252,243,216,0.08)" stroke="rgba(252,243,216,0.22)"/>
    <text class="count-10" x="102" y="22" text-anchor="middle" font-family="JetBrains Mono, ui-monospace, monospace" font-size="10" font-weight="600" fill="#FCF3D8">10.4k</text>
    <text class="count-101" x="102" y="22" text-anchor="middle" font-family="JetBrains Mono, ui-monospace, monospace" font-size="10" font-weight="700" fill="#FFD94A">10.5k</text>
  </g>

  <!-- cursor -->
  <g class="cursor">
    <path d="M0 0 L0 14 L4 11 L7 16 L10 14.5 L6.5 9.5 L11 9.5 Z" fill="#FCF3D8" stroke="#2A121B" stroke-width="1" stroke-linejoin="round"/>
  </g>
<style xmlns="" class="darkreader darkreader--fallback">html, body, body :not(iframe) {
    background-color: var(--darkreader-background-ffffff, #181a1b) !important;
    border-color: var(--darkreader-border-404040, #776e62) !important;
    color: var(--darkreader-text-000000, #e8e6e3) !important;
}
div[style*="background-color: rgb(135, 135, 135)"] {
    background-color: #878787 !important;
}</style></svg>