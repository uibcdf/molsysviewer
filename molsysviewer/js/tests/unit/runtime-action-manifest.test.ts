import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import ts from "typescript";

import {
    ACTION_CATEGORIES,
    DATA_PLANE_ACTIONS,
    POPUP_ACTIONS,
    RAW_ACTIONS,
} from "../../src/messages/runtime-actions";

type Sender = {
    action: string;
    direction: string | null;
    file: string;
    line: number;
};

function sourceFiles(root: string): string[] {
    return fs.readdirSync(root, { withFileTypes: true }).flatMap(entry => {
        const candidate = path.join(root, entry.name);
        if (entry.isDirectory()) return sourceFiles(candidate);
        return entry.name.endsWith(".ts") ? [candidate] : [];
    });
}

function terminalCallName(expression: ts.LeftHandSideExpression): string | null {
    if (ts.isIdentifier(expression)) return expression.text;
    if (ts.isPropertyAccessExpression(expression)) return expression.name.text;
    return null;
}

function stringProperty(
    source: ts.SourceFile,
    object: ts.ObjectLiteralExpression,
    name: string,
): string | null {
    for (const property of object.properties) {
        if (!ts.isPropertyAssignment(property)) continue;
        if (property.name.getText(source).replace(/["']/g, "") !== name) continue;
        return ts.isStringLiteral(property.initializer) ? property.initializer.text : null;
    }
    return null;
}

function staticRuntimeSenders(): { browser: Sender[]; popup: Sender[] } {
    const browser: Sender[] = [];
    const popup: Sender[] = [];
    const root = path.resolve(process.cwd(), "src");

    for (const file of sourceFiles(root)) {
        const source = ts.createSourceFile(
            file,
            fs.readFileSync(file, "utf8"),
            ts.ScriptTarget.Latest,
            true,
        );
        const visit = (node: ts.Node) => {
            if (ts.isCallExpression(node)) {
                const name = terminalCallName(node.expression);
                const first = node.arguments[0];
                const line = source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1;
                const relative = path.relative(process.cwd(), file);

                if (
                    (name === "notify" || name === "sendToPython")
                    && first
                    && ts.isObjectLiteralExpression(first)
                ) {
                    const action = stringProperty(source, first, "event");
                    if (action) browser.push({ action, direction: null, file: relative, line });
                }

                if (name === "sendToHost" && first && ts.isStringLiteral(first)) {
                    const action = first.text;
                    const direction =
                        action === "molsysviewer-sync-op"
                        || action === "molsysviewer-popup-interaction"
                            ? "command"
                            : "event";
                    popup.push({ action, direction, file: relative, line });
                }

                if (
                    (name === "send" || name === "sendTo")
                    && ts.isPropertyAccessExpression(node.expression)
                    && node.expression.expression.getText(source) === "popupMgr"
                ) {
                    const actionArg = name === "sendTo" ? node.arguments[1] : first;
                    if (actionArg && ts.isStringLiteral(actionArg)) {
                        const action = actionArg.text;
                        const direction = action === "molsysviewer-sync-camera" ? "event" : "projection";
                        popup.push({ action, direction, file: relative, line });
                    }
                }
            }
            ts.forEachChild(node, visit);
        };
        visit(source);
    }
    return { browser, popup };
}

test("every static browser sender is declared in the shared runtime manifest", () => {
    const { browser } = staticRuntimeSenders();
    assert.ok(browser.length > 0, "the AST scan must find browser senders");
    const declared = new Set([
        ...ACTION_CATEGORIES.keys(),
        ...RAW_ACTIONS,
        ...DATA_PLANE_ACTIONS,
    ]);
    const missing = browser.filter(sender => !declared.has(sender.action));
    assert.deepStrictEqual(
        missing,
        [],
        `undeclared browser senders: ${missing.map(x => `${x.action}@${x.file}:${x.line}`).join(", ")}`,
    );
});

test("every static popup sender is declared for the direction it emits", () => {
    const { popup } = staticRuntimeSenders();
    assert.ok(popup.length > 0, "the AST scan must find popup senders");
    const invalid = popup.filter(sender => !POPUP_ACTIONS.get(sender.action)?.has(sender.direction!));
    assert.deepStrictEqual(
        invalid,
        [],
        `invalid popup senders: ${invalid.map(x => `${x.action}:${x.direction}@${x.file}:${x.line}`).join(", ")}`,
    );
});
