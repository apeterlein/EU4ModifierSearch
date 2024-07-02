window.addEventListener("DOMContentLoaded", () => {
	"use strict";

	function highlight(parent, text, groups) {
		while (true) {
			let match, high;
			for (const i in groups) {
				const c = groups[i].reg.exec(text);
				if (c && (!match || c.index < match.index)) {
					match = c;
					high = groups[i].high;
				}
			}
			if (!match) break;
			parent.append(text.slice(0, match.index));
			const span = document.createElement("span");
			span.classList.add(high);
			span.append(match[0]);
			parent.append(span);
			text = text.slice(match.index + match[0].length);
		}
		parent.append(text);
	}

	const data = JSON.parse(ArchUtils.bz2.decode(atob(window.modifiers)));
	const modifiers = Object.keys(data.__modifiers).sort();
	const types = Object.keys(data).sort();
	const sep = String.fromCharCode(31);
	
	const suggBox = document.getElementById("suggestion-box");
	const searchBox = document.getElementById("search");
	const resBox = document.getElementById("result-box");
	const schIcon = document.getElementById("search-icon");
	const colIcon = document.getElementById("collapse-icon");
	const expIcon = document.getElementById("expand-icon");

	types.forEach((type) => {
		if (type.startsWith("__")) return;
		const box = document.createElement("div");
		box.classList.add("result-type");
		const bar = document.createElement("div");
		bar.classList.add("result-bar");
		const col = colIcon.cloneNode(true);
		col.id = "";
		bar.append(col);
		const exp = expIcon.cloneNode(true);
		exp.id = "";
		exp.addEventListener("click", () => {
			exp.parentElement.parentElement.querySelector(".result-coll").classList.remove("hidden");
			exp.classList.add("hidden");
			col.classList.remove("hidden");
		});
		col.addEventListener("click", () => {
			col.parentElement.parentElement.querySelector(".result-coll").classList.add("hidden");
			exp.classList.remove("hidden");
			col.classList.add("hidden");
		});
		exp.classList.remove("hidden");
		bar.append(exp);
		const name = document.createElement("div");
		name.classList.add("type-name");
		name.innerHTML = type;
		bar.append(name);
		const count = document.createElement("div");
		count.classList.add("result-count", "gray");
		count.innerHTML = 0;
		bar.append(count);
		box.append(bar);
		const coll = document.createElement("div");
		coll.classList.add("result-coll", "hidden");
		box.append(coll);
		box.dataset.type = type;
		resBox.append(box);
	});

	schIcon.addEventListener("click", () => {
		const search = searchBox.value.toLowerCase();
		window.location.hash = search;
		const groups = [
			{ reg: new RegExp("(?<!_)" + search + "(?=[ \t]*=)"), high: "highlight" }, 
			{ reg: /has_dlc ?= ?"[^"]+"/, high: "warning" }
		];
		if (!modifiers.includes(search)) return;
		document.querySelectorAll(".result").forEach((elm) => {
			elm.remove();
		});
		document.querySelectorAll(".result-count").forEach((elm) => {
			elm.innerHTML = 0;
			elm.classList.add("gray");
		});
		data.__modifiers[search].forEach((source) => {
			const [type, modifier] = source.split(sep);
			const text = data[type][modifier];
			const box = document.querySelector(".result-type[data-type='" + type + "']");
			const count = box.querySelector(".result-count")
			count.innerHTML++
			count.classList.remove("gray");
			const coll = box.querySelector(".result-coll");
			const res = document.createElement("div");
			res.classList.add("result");
			const line = document.createElement("div");
			line.classList.add("result-line");
			const src = document.createElement("span");
			src.classList.add("result-src");
			line.append(src);
			res.append(line);
			src.innerHTML = text[0];
			for (let i = 1; i < text.length; i++) {
				const line = document.createElement("div");
				line.classList.add("result-line");
				const [tabs, ln] = text[i].split(sep);
				for (let j = 0; j < tabs; j++) {
					let tab = document.createElement("span");
					tab.classList.add("result-tab");
					line.append(tab);
				}
				highlight(line, ln, groups);
				res.append(line);
			}
			coll.append(res);
		});
	});
	searchBox.addEventListener("focusin", () => {
		suggBox.classList.remove("hidden");
		searchBox.dispatchEvent(new Event("input"));
	});
	searchBox.addEventListener("focusout", () => {
		suggBox.classList.add("hidden");
	});
	searchBox.addEventListener("input", () => {
		const val = searchBox.value.toLowerCase();
		const groups = [{ reg: new RegExp(val), high: "highlight" }];
		suggBox.innerHTML = "";
		if (!val) return;
		let count = 0;
		for (const i in modifiers) {
			let mod = modifiers[i];
			if(mod.includes(val)) {
				let suggestion = document.createElement("div");
				suggestion.dataset.modifier = mod;
				suggestion.addEventListener("mousedown", () => {
					searchBox.value = suggestion.dataset.modifier;
					schIcon.dispatchEvent(new Event("click"));
				});
				suggestion.classList.add("suggestion");
				highlight(suggestion, mod, groups);
				suggBox.append(suggestion);
				if (++count >= 20) break;
			}
		}
	});
	searchBox.addEventListener("keypress", (event) => {
		if (event.key === "Enter") {
			searchBox.dispatchEvent(new Event("focusout"));
			schIcon.dispatchEvent(new Event("click"));
		}
	});

	document.getElementById("version").innerHTML = data.__version;
	if (window.location.hash) {
		searchBox.value = window.location.hash.replace("#", "");
		schIcon.dispatchEvent(new Event("click"));
	}

	document.getElementById("loading").classList.add("hidden");
	document.getElementById("main-content").classList.remove("hidden");
});