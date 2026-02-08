
export async function fetchMetadata() {
    const result = await (await fetch(`/config`)).json()
    return result
}

