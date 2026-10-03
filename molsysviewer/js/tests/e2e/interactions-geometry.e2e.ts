import { chromium } from "./e2e-browser";
import { runInteractionsSuite } from "./interactions-subpanel-scenarios";

runInteractionsSuite(chromium, "geometry").catch(error => { console.error(error); process.exit(1); });
