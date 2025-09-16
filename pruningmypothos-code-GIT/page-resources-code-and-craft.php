<?php
/*
Template Name: Code & Craft Resource Page
*/
get_header();
?>

<section class="resource-section">
  <div class="container">

    <!-- HERO -->
    <div class="resource-hero-section fade-in">
      <h1 class="resource-title">Code & Craft</h1>
      <p class="resource-subtitle">Builds & Breakpoints</p>
      <p class="resource-intro">
        This isn’t about learning to code—it’s about learning how to <strong>document</strong> what matters. 
        <em>Code & Craft</em> curates practical guides, reference structures, and real-world examples that help writers and developers work 
        <strong>together</strong>, not just in parallel.
      </p>
    </div>

    <!-- CARDS SECTION -->
    <div class="resource-cards-section fade-in">
      <div class="resource-grid">
        <!-- Example Resource Card -->
        <div class="resource-card">
          <h3 class="resource-card-title">REAPER Install Guide</h3>
          <p class="resource-card-description">
            A version-aware, beginner-focused install doc for REAPER DAW. Highlights structure, clarity, and learning curve sensitivity.
          </p>
          <a href="/docs/getting-started-with-reaper" class="resource-btn">→ View Guide</a>
        </div>

        <div class="resource-card">
          <h3 class="resource-card-title">Markdown Best Practices</h3>
          <p class="resource-card-description">
            A quick reference to using Markdown like a documentation pro. Includes table formatting, emphasis rules, and more.
          </p>
          <a href="/docs/markdown-style-guide" class="resource-btn">→ View Guide</a>
        </div>
      </div>
    </div>

    <!-- QUOTE BLOCK -->
    <div class="resource-tip-section fade-in">
      <blockquote class="resource-quote">
        🧠 <em>Good documentation isn’t about writing more. It’s about writing just enough—at the right time—for the right person.</em>
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
