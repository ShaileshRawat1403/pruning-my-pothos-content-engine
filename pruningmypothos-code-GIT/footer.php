<footer class="boho-footer" role="contentinfo">
  <div class="footer-container">

    <!-- NEWSLETTER SECTION -->
    <section class="newsletter-section">
      <div class="container">
        <h2>Stay Inspired</h2>
        <p>Join our mailing list for exclusive insights and updates.</p>
        <form action="#" method="POST" aria-label="Newsletter Signup Form">
          <input type="email" name="email" placeholder="Enter your email" required>
          <button type="submit" class="cta-btn">Subscribe</button>
        </form>
      </div>
    </section>

    <div class="footer-content">

      <!-- Footer Branding -->
      <div class="footer-brand">
        <h3>Pruning My Pothos</h3>
        <p>Personal Ponderings on Purpose, Passion, Philosophy, People, Plants & Pets.</p>
      </div>

      <!-- Footer Links -->
      <div class="footer-links">
        <h4>Quick Links</h4>
        <ul>
          <li><a href="<?php echo home_url(); ?>">Home</a></li>
          <li><a href="<?php echo home_url('/about'); ?>">About</a></li>
          <li><a href="<?php echo home_url('/resources'); ?>">Resources</a></li>
          <li><a href="<?php echo home_url('/contact'); ?>">Contact</a></li>
        </ul>
      </div>

      <!-- Footer Social Links -->
      <div class="footer-social">
        <h4>Follow</h4>
        <ul class="social-links">
          <li><a href="#" aria-label="Instagram">Instagram</a></li>
          <li><a href="#" aria-label="LinkedIn">LinkedIn</a></li>
        </ul>
      </div>

    </div> <!-- .footer-content -->

  </div> <!-- .footer-container -->

  <div class="footer-bottom">
    <p>&copy; <?php echo date('Y'); ?> Pruning My Pothos. All rights reserved.</p>
  </div>
</footer>

<!-- Scroll to Top Button -->
<button id="scrollToTopBtn" aria-label="Scroll to Top">↑</button>

<?php wp_footer(); ?>
</body>
</html>
