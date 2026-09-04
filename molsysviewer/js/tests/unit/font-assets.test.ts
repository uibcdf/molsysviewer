import assert from "node:assert/strict";
import test from "node:test";

import { VARELA_ROUND_WOFF2_DATA_URL } from "../../src/assets/varela-round/font-data";

test("Varela Round is an embedded WOFF2 resource without a network dependency", () => {
    assert.match(VARELA_ROUND_WOFF2_DATA_URL, /^data:font\/woff2;base64,/);
    assert.doesNotMatch(VARELA_ROUND_WOFF2_DATA_URL, /https?:/);
    const encoded = VARELA_ROUND_WOFF2_DATA_URL.split(",", 2)[1];
    const font = Buffer.from(encoded, "base64");
    assert.equal(font.subarray(0, 4).toString("ascii"), "wOF2");
    assert.equal(font.byteLength, 22_948);
});
