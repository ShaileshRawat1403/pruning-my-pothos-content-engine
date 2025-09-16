<?php
/*
Template Name: Contact Page
*/
get_header();
?>

<section class="contact-hero">
  <div class="container">
    <h1>Let’s Connect Thoughtfully</h1>
    <p>Whether you want to say hi, subscribe to sticky notes, or get published—this is your space.</p>
  </div>
</section>

<section class="contact-main">
  <div class="container">
    
    <!-- Say Hi Form -->
    <div class="contact-block">
      <h2>👋 Just Say Hi</h2>
      <form action="<?php echo esc_url(admin_url('admin-post.php')); ?>" method="post" class="contact-form">
        <input type="hidden" name="action" value="process_contact_form">

        <label for="name">Name</label>
        <input type="text" name="name" id="name" required>

        <label for="email">Email</label>
        <input type="email" name="email" id="email" required>

        <label for="message">Message</label>
        <textarea name="message" id="message" rows="4" required></textarea>

        <button type="submit" class="btn-submit">Send Message</button>
      </form>
    </div>

    <!-- Newsletter Signup -->
    <div class="contact-block">
      <h2>🧠 Get Sticky Notes (Newsletter)</h2>
      <p>Receive thoughtful updates. No spam. No scroll traps.</p>
      <form action="https://pruningmypothos.us3.list-manage.com/subscribe/post?u=9c919c893f094fbe48167563b&amp;id=ec2c5a4bb0" method="post" target="_blank" class="newsletter-form">
        <input type="email" name="EMAIL" placeholder="Your Email" required>
        <button type="submit" class="btn-subscribe">→ Subscribe</button>
      </form>
    </div>

    <!-- Publish Invite -->
    <div class="contact-block">
      <h2>✍️ Want to Get Published?</h2>
      <p>If you have something to share—writing, a reflection, a resource—email me at:</p>
      <a href="mailto:sprout@pruningmypothos.com" class="email-link">hello@pruningmypothos.com</a>
    </div>

  </div>
</section>

<style>
  .contact-hero {
    background: #fefaf6;
    text-align: center;
    padding: 100px 20px 60px;
  }

  .contact-hero h1 {
    font-size: 2.5rem;
    font-family: 'Space Grotesk', sans-serif;
    margin-bottom: 10px;
  }

  .contact-hero p {
    font-size: 1.1rem;
    color: #555;
    max-width: 600px;
    margin: 0 auto;
  }

  .contact-main {
    padding: 60px 20px 100px;
    background: #fff;
  }

  .contact-block {
    max-width: 600px;
    margin: 0 auto 60px;
    text-align: center;
  }

  .contact-block h2 {
    font-size: 1.5rem;
    margin-bottom: 10px;
  }

  .contact-block p {
    font-size: 1rem;
    color: #666;
    margin-bottom: 20px;
  }

  .contact-form label {
    display: block;
    text-align: left;
    margin-bottom: 5px;
    font-weight: 500;
  }

  .contact-form input,
  .contact-form textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #ccc;
    border-radius: 6px;
    margin-bottom: 20px;
    font-size: 1rem;
  }

  .btn-submit,
  .btn-subscribe {
    background: #e74c3c;
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: background 0.2s ease;
  }

  .btn-subscribe {
    background: #007bff;
  }

  .btn-submit:hover,
  .btn-subscribe:hover {
    opacity: 0.9;
  }

  .newsletter-form input {
    width: 70%;
    padding: 10px;
    margin-right: 8px;
    border-radius: 6px;
    border: 1px solid #ccc;
    font-size: 1rem;
  }

  .email-link {
    font-family: monospace;
    display: inline-block;
    margin-top: 10px;
    color: #333;
    font-size: 1.1rem;
    text-decoration: underline;
  }

  @media (max-width: 600px) {
    .newsletter-form input {
      width: 100%;
      margin-bottom: 10px;
    }

    .newsletter-form {
      display: flex;
      flex-direction: column;
    }

    .btn-subscribe {
      width: 100%;
    }
  }
</style>

<?php get_footer(); ?>
