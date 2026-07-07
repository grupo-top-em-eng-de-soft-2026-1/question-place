const protectedImageUrls = new WeakMap();

async function loadProtectedImage(path, image, token) {
    const response = await fetch(path, {
        headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
        return response;
    }

    const previousUrl = protectedImageUrls.get(image);
    if (previousUrl) {
        URL.revokeObjectURL(previousUrl);
    }

    const objectUrl = URL.createObjectURL(await response.blob());
    protectedImageUrls.set(image, objectUrl);
    image.src = objectUrl;
    return response;
}
