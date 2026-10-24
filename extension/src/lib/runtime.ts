// The website sets this attribute; extension pages keep their existing behavior.
export const IS_WEBSITE = typeof document !== "undefined" && document.documentElement.dataset.client === "website";
export const assetUrl = (name: string) => `${IS_WEBSITE ? "/web-assets" : ""}/${name}`;
