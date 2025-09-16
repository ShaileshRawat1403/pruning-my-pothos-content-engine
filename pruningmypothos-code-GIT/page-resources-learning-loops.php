<?php
/*
Template Name: Learning Loops Resource Page
*/
get_header();
?>

<section class="resource-section">
  <div class="container">

    <!-- HERO -->
    <div class="resource-hero-section fade-in">
      <h1 class="resource-title">Learning Loops</h1>
      <p class="resource-subtitle">Repeat Until Known</p>
      <h3 class="resource-caption">Nothing truly changes until you notice what repeats.</h3>
      <p class="resource-intro">
        Learning isn’t linear—and neither is documentation. <em>Learning Loops</em> is a space for unfinished thoughts, updated drafts,
        and practical insights earned through iteration. It's not a library; it’s a changelog of becoming.
      </p>
    </div>

    <!-- CARDS SECTION -->
    <div class="resource-cards-section fade-in">
      <div class="resource-grid">
        <!-- Example Resource Card -->
        <div class="resource-card">
          <h3 class="resource-card-title">Doc Feedback Loops</h3>
          <p class="resource-card-description">
            A guide to building effective review processes and integrating feedback from developers, users, and stakeholders.
          </p>
          <a href="/docs/documentation-feedback-loops" class="resource-btn">→ View Guide</a>
        </div>

        <div class="resource-card">
          <h3 class="resource-card-title">Version Notes Template</h3>
          <p class="resource-card-description">
            A modular structure for release notes that helps writers communicate updates clearly—without boring their readers.
          </p>
          <a href="/docs/version-notes-template" class="resource-btn">→ View Template</a>
        </div>
      </div>
    </div>

    <!-- QUOTE BLOCK -->
    <div class="resource-tip-section fade-in">
      <blockquote class="resource-quote">
        🧠 <em>We don’t learn by doing it right. We learn by noticing what went wrong—documenting it, and repeating smarter next time.</em>
      </blockquote>
    </div>

    <!-- BACK LINK -->
    <div class="back-link-section fade-in">
      <a href="/resources" class="back-link">← Back to All Resources</a>
    </div>

  </div>
</section>

<?php get_footer(); ?>

<style>
  .resource-title {
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 0.2em;
  }
  .resource-subtitle {
    font-size: 1.25rem;
    font-family: monospace;
    color: var(--accent-color);
    margin-bottom: 1em;
  }
  .resource-intro {
    max-width: 700px;
    margin: 0 auto;
    text-align: center;
    font-size: 1.1rem;
  }
  .resource-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
  }
  .resource-card {
    padding: 1.5rem;
    background: #fff;
    border: 1px solid #eaeaea;
    border-radius: 1rem;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s ease;
  }
  .resource-card:hover {
    transform: translateY(-5px);
  }
  .resource-card-title {
    font-size: 1.2rem;
    margin-bottom: 0.5rem;
  }
  .resource-card-description {
    font-size: 1rem;
    margin-bottom: 1rem;
    color: var(--secondary-color);
  }
  .resource-btn {
    text-decoration: none;
    color: var(--accent-color);
    font-weight: bold;
    border-bottom: 1px solid transparent;
    transition: all 0.2s;
  }
  .resource-btn:hover {
    border-color: var(--accent-color);
  }
  .resource-quote {
    font-size: 1rem;
    font-style: italic;
    text-align: center;
    padding: 2rem 1rem;
    background: #f9f9f9;
    border-left: 4px solid var(--accent-color);
    margin-top: 3rem;
  }
  .back-link {
    display: inline-block;
    margin-top: 2rem;
    font-size: 0.95rem;
    color: var(--primary-color);
    text-decoration: none;
    border-bottom: 1px solid transparent;
  }
  .back-link:hover {
    border-color: var(--primary-color);
  }
</style>
