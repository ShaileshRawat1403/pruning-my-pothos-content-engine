<?php
/*
Template Name: Reflection & Growth Resource Page
*/
get_header();
?>

<section class="resource-section">
  <div class="container">

    <!-- HERO -->
    <div class="resource-hero-section fade-in">
      <h1 class="resource-title">Reflection & Growth</h1>
      <p class="resource-subtitle">Debugging the Self</p>
      <h3 class="resource-caption">The self you avoid is the draft that needs editing.</h3>
      <p class="resource-intro">
        This space isn’t about self-improvement hacks. It’s a sandbox for awareness, articulation, and documenting your evolution. 
        <em>Reflection & Growth</em> gathers frameworks, journaling models, and insight templates to help you examine your thoughts like a dev reads logs—calmly, curiously, and without blame.
      </p>
    </div>

    <!-- CARDS SECTION -->
    <div class="resource-cards-section fade-in">
      <div class="resource-grid">
        <!-- Example Resource Card -->
        <div class="resource-card">
          <h3 class="resource-card-title">Sticky Note Debug Sheet</h3>
          <p class="resource-card-description">
            A printable, analog-style debugging template to untangle recurring thoughts, blockers, and emotion triggers.
          </p>
          <a href="/docs/sticky-note-debug-sheet" class="resource-btn">→ View Template</a>
        </div>

        <div class="resource-card">
          <h3 class="resource-card-title">Journaling Prompts for Technical Writers</h3>
          <p class="resource-card-description">
            A set of questions designed to unpack your working patterns, voice, and mindset as a communicator in technical spaces.
          </p>
          <a href="/docs/journaling-prompts-writers" class="resource-btn">→ View Prompts</a>
        </div>
      </div>
    </div>

    <!-- QUOTE BLOCK -->
    <div class="resource-tip-section fade-in">
      <blockquote class="resource-quote">
        🧠 <em>Growth isn't an upgrade. It's a patch note. Small fixes. Ongoing versions. Debugging what no longer serves.</em>
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
