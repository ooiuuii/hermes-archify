// Run inside the supported browser Node session with its existing tab and CDP.
// Captures ordinary reading/scrolling of the unmodified native-skill HTML.
import fs from 'node:fs/promises';
import {recordLive} from '../v4/record-live.mjs';

export async function recordNative({tab, cdp, directory}) {
  const scrolls = [];
  const locate = async text => tab.playwright.evaluate(text => {
    const el = Array.from(document.querySelectorAll('svg text.title,.card h2'))
      .find(el => el.textContent === text);
    if (!el) throw Error('Missing observed label: ' + text);
    const r = el.getBoundingClientRect();
    if (r.top < 0 || r.bottom > innerHeight || r.left < 0 || r.right > innerWidth)
      throw Error('Reading target is outside the viewport: ' + text);
    return {x:r.x+r.width/2,y:r.y+r.height/2};
  }, text);
  const capture = recordLive({tab, cdp, directory, durationMs:27000,
    actions: async io => {
      const point = async (time, text, duration=900) => {
        await io.at(time);
        await io.move(await locate(text), duration);
      };
      const scroll = async (time, deltaY) => {
        await io.at(time);
        const pos = await locate('Tool Registry');
        await io.move(pos, 450);
        await cdp.send('Input.dispatchMouseEvent', {
          type:'mouseWheel', ...pos, deltaX:0, deltaY
        });
        scrolls.push({scheduled_ms:time, type:'mouseWheel', ...pos, deltaX:0, deltaY});
      };
      await io.snapshot('01-native-top');
      await point(900, 'Hermes CLI');
      await point(3100, 'AIAgent 运行时');
      await point(5300, 'Conversation / Model Loop');
      await point(7600, 'Transport → 模型 / Provider API', 1100);
      await point(9900, 'Tool-call Executor');
      await point(11700, 'Dispatcher + Guardrails');
      await scroll(13500, 450);
      await io.at(15000);
      await io.snapshot('02-native-handlers');
      await point(15400, '文件工具');
      await point(17200, 'hermes-archify 插件');
      await scroll(19000, 380);
      await io.at(20500);
      await io.snapshot('03-native-source-summary');
      await point(20800, '核心循环');
      await point(23200, '统一窄腰');
      await point(25100, 'hermes-archify 的接入点');
    }
  });
  // A completely static page may not emit a first frame until a new paint.
  // This actual pointer event starts the capture; it is not a synthetic frame.
  const wake = (async () => {
    await new Promise(resolve => setTimeout(resolve, 1200));
    await cdp.send('Input.dispatchMouseEvent', {type:'mouseMoved',x:49,y:170});
  })();
  const [result] = await Promise.all([capture, wake]);
  const path = `${directory}/capture.json`;
  const report = JSON.parse(await fs.readFile(path, 'utf8'));
  report.scroll_events = scrolls;
  report.native_reading = 'Real pointer input and ordinary browser scrolling; no diagram interactivity was added.';
  await fs.writeFile(path, JSON.stringify(report, null, 2));
  return {...result, scroll_events:scrolls.length};
}
