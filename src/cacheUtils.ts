import persistentCache from "persistent-cache";

// Cache
export const apiKeyCache = persistentCache({
	name: "apiKey",
	base: "./.romRenamerCache",
});

export const titleCache = persistentCache({
	name: "title",
	base: "./.romRenamerCache",
});

export const renameHistoryCache = persistentCache({
	name: "renameHistory",
	base: "./.romRenamerCache",
});
