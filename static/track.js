// Sends a GA4 "affiliate_click" event for every referral-link click.
// In GA4, mark affiliate_click as a Key event so it appears as a conversion.
document.addEventListener('click', function (ev) {
  var a = ev.target.closest && ev.target.closest('a[data-aff]');
  if (!a || typeof gtag !== 'function') return;
  gtag('event', 'affiliate_click', {
    placement: a.getAttribute('data-aff'),
    page_path: location.pathname,
    transport_type: 'beacon'
  });
});
