let currentDomain = null;

const DEBUG = false;

function debugLog(message, data = null) {
    if (DEBUG) {
        console.log(`[MAS Firefox Submod] ${message}`, data || '');
    }
}

function extractDomain(url) {
    try {
        return new URL(url).hostname.replace(/^www\./, '');
    } catch {
        return null;
    }
}

async function updateDomain() {
    const tabs = await browser.tabs.query({active: true, currentWindow: true});
    if (tabs[0] && tabs[0].url) {
        const newDomain = extractDomain(tabs[0].url);
        if (newDomain && newDomain !== currentDomain) {
            currentDomain = newDomain;
            sendDomain(newDomain);
        }
    }
}


async function sendDomain(domain) {
    debugLog('Sending domain', { domain, timestamp: new Date().toISOString() });

    const endpoints = [
        { port: 9163, name: 'main' },
        { port: 9162, name: 'reserved' }
    ];

    for (const endpoint of endpoints) {
        try {
            const url = `http://localhost:${endpoint.port}/domain`;
            debugLog(`Attemting send on ${endpoint.name} port`, { url });

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    domain: domain,
                    timestamp: new Date().toISOString(),
                    source: 'browser_extension'
                })
            });

            if (response.ok) {
                const responseData = await response.json();
                debugLog(`Successfuly sended on ${endpoint.port} port`, responseData);
                return;
            } else {
                debugLog(`HTTP error on ${endpoint.port} port`, { status: response.status });
            }
        } catch (error) {
            debugLog(`Sending error on ${endpoint.port} port`, error.message);

        }
    }

    debugLog("Error: Couldn't send to both ports");
}

browser.tabs.onActivated.addListener(updateDomain);
browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (tab.active && changeInfo.url) updateDomain();
});

browser.tabs.query({active: true, currentWindow: true}).then(updateDomain);
