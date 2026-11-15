# Ghostflame discovery prototype

Open `index.html` directly in your browser. No install, server, API key, or backend is needed. Google Fonts is optional; system fonts work offline. Dashboard images are embedded in the copied HTML.

This isolated prototype copies `../../ghostflame-home.html`, the existing standalone dashboard mockup that shares the React frontend's layout and palette. The production frontend is unchanged. Existing dashboard controls and figures are inherited mockup content, not refreshed research results. Only the discovery feature is being tested here.

## Try it

1. Leave the dashboard visible for 10 seconds. A randomly selected object appears, jiggles three times, then gains a dismiss cross.
2. Click it to open a fact card. Click the same topic again or use **Another discovery**: the next fact differs. Each topic exhausts a shuffled bag before repeating, including at cycle boundaries.
3. Close with Escape or the close button. Dismiss the floating object; **Discover** still opens all six topics. Dismissal lasts for this browser-tab session, including reloads.
4. Expand **Discovery prototype** at bottom left. **Simulation running** pauses the remaining delay and hides discovery UI; turning it off resumes the timer. This is a state test, not a fire simulation.
5. **Replay 10-second arrival** clears dismissal and resets the timer. It does not erase fact progress.
6. Try the dashboard's light/dark controls and a narrow window. Reduced-motion preferences skip the jiggle and show the cross immediately. Hidden browser tabs pause the timer.

## Content and integration

- Six SVG object illustrations; 13 curated cards. Each card links directly to NASA. Historical spinoffs are explicitly dated. Source wording checked on 2026-11-14.
- Facts and shuffle behavior: `discovery.js`. Styling: `discovery.css`, using the existing dashboard CSS variables.
- Call `window.ghostflameDiscovery.setSimulationRunning(true)` when the real simulation starts and `false` when it ends. Alternatively dispatch `new CustomEvent('ghostflame:simulation', {detail: {running: true}})`.
- This standalone page is always the dashboard. For React integration, mount the component only on the dashboard route and add cleanup for intervals/listeners on unmount.
- Fact progress uses `localStorage`; dismissal uses `sessionStorage`. If storage is blocked, the feature falls back to memory for the loaded page.
- Native modal dialog provides keyboard focus containment and Escape handling. Fact cards are educational, not emergency instructions.
- This is a small representative content set; detailed comparisons of extinguisher agents and detector technologies can be added after sourcing.
