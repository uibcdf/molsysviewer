/** Reusable local search state and native field; never emits scene actions. */
export class ListSearch {
    query = "";
    matches(text: string): boolean { return text.toLocaleLowerCase().includes(this.query.toLocaleLowerCase().trim()); }
    field(label: string, onInput: () => void): HTMLInputElement {
        const input = document.createElement("input"); input.type = "search"; input.value = this.query;
        input.placeholder = label; input.setAttribute("aria-label", label);
        Object.assign(input.style, { width: "100%", boxSizing: "border-box", color: "inherit", background: "rgba(0,0,0,.2)", border: "1px solid #555", borderRadius: "5px", padding: "6px" });
        input.oninput = () => { this.query = input.value; onInput(); };
        return input;
    }
}
