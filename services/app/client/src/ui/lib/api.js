export async function getJson(url) {
    const response = await fetch(url);
    if (!response.ok)
        throw new Error(`Request failed: ${response.status}`);
    return response.json();
}
