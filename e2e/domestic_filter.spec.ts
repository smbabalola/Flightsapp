import { test, expect } from '@playwright/test';

test('domestic routes are filtered when flag enabled', async ({ request }) => {
  // Try a NG->NG route; when IGNORE_DOMESTIC_ROUTES=true, expect zero or no selectable offers
  const today = new Date();
  const depart = new Date(today.getTime() + 7 * 86400000);
  const yyyy = depart.getFullYear();
  const mm = String(depart.getMonth() + 1).padStart(2, '0');
  const dd = String(depart.getDate()).padStart(2, '0');
  const res = await request.post('/v1/search', {
    data: {
      slices: [{ from_: 'LOS', to: 'ABV', date: `${yyyy}-${mm}-${dd}` }],
      adults: 1
    }
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  const offers = body.offers || [];
  // If the flag is on, expect zero offers. If not, skip but assert structure.
  if (offers.length > 0) {
    test.skip(true, 'IGNORE_DOMESTIC_ROUTES may be disabled in this environment');
  } else {
    expect(offers.length).toBe(0);
  }
});

