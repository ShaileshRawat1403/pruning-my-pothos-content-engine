<?php
/*
Template Name: About Page
*/

// ✅ JSON-LD Schema for About Page
$about_schema = [
  "@context" => "https://schema.org",
  "@type" => "AboutPage",
  "name" => "About Pruning My Pothos",
  "url" => home_url('/about/'),
  "inLanguage" => "en",
  "description" => "Explore the metaphor, people, and purpose behind Pruning My Pothos — a creative rebellion rooted in tech transformation, existential clarity, and meaningful growth.",
  "publisher" => [
    "@type" => "Organization",
    "name" => "PruningMyPothos",
    "url" => home_url(),
    "logo" => [
      "@type" => "ImageObject",
      "url" => "https://pruningmypothos.com/wp-content/uploads/2025/06/logo-pruning-my-pothos.png",
      "width" => 512,
      "height" => 512
    ]
  ],
  "mainEntity" => [
    "@type" => "WebPageElement",
    "name" => "Team, Pothos Philosophy, Core Beliefs",
    "description" => "Meet the makers of metaphor: Thought Pruner, Metaphor Gardener, and two philosophical dogs. Explore why growth begins with restraint."
  ]
];
?>

<!-- Inject Schema in Head -->
<script type="application/ld+json">
  <?php echo json_encode($about_schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE); ?>
</script>

<?php get_header(); ?>

<section class="about-section">
  <div class="container">

    <!-- HERO INTRO -->
    <div class="about-intro fade-in">
      <h1 class="page-title">About Pruning My Pothos</h1>
      <p><em>Some people write manifestos. We prune plants.</em></p>
      <p>This isn’t a blog. It’s a slow, leafy rebellion against noise — and a quiet practice of letting go.</p>
    </div>

    <!-- OUR STORY -->
    <div class="about-story-section fade-in split-layout">
      <div class="story-image">
        <img src="https://pruningmypothos.com/wp-content/uploads/2025/06/about-us-pruningmypothos.jpg" alt="The Pruning My Pothos family" class="story-img" loading="lazy">
      </div>
      <div class="story-text">
        <h2>Why We Prune</h2>
        <p>Pruning My Pothos started as a quiet reflection on growth — not the loud, optimized kind, but the kind that sprawls. We found poetry in pothos leaves, and therapy in letting go.</p>
        <p>This space is our journal: part philosophy, part creative mulch, part garden of existential weeds.</p>
      </div>
    </div>

    <!-- MEET THE CREW -->
    <div class="about-team-section fade-in">
      <h2>Meet the Minds (and Mutts)</h2>
      <div class="team-grid">

        <div class="team-card">
          <img src="https://pruningmypothos.com/wp-content/uploads/2025/03/pruningmypothos-1.jpg" alt="Shailesh" class="team-img">
          <h3>Shailesh</h3>
          <p class="team-role">Thought Pruner</p>
          <p class="team-quote">"placeholder."</p>
        </div>

        <div class="team-card">
          <img src="https://pruningmypothos.com/wp-content/uploads/2025/06/ananya-pruning-my-pothos-scaled.jpg" alt="Wife" class="team-img">
          <h3>Ananya</h3>
          <p class="team-role">Metaphor Gardener</p>
          <p class="team-quote">"Finds philosophy in pothos roots. Grows more than just plants."</p>
        </div>

        <div class="team-card">
          <img src="https://pruningmypothos.com/wp-content/uploads/2025/03/SIMBA.jpg" alt="Simba" class="team-img">
          <h3>Simba</h3>
          <p class="team-role">Existential Barker</p>
          <p class="team-quote">"Growls at nothing. Like a true philosopher."</p>
        </div>

        <div class="team-card">
          <img src="https://pruningmypothos.com/wp-content/uploads/2025/03/KUTTUSH-scaled-e1743243052435.jpg" alt="Kuttush" class="team-img">
          <h3>Kuttush</h3>
          <p class="team-role">Leaf Thief</p>
          <p class="team-quote">"Stole a pothos once. No regrets."</p>
        </div>

      </div>
    </div>

    <!-- POTHOS PHILOSOPHY SECTION -->
    <div class="about-story-section fade-in split-layout">
      <div class="story-image">
        <img src="https://pruningmypothos.com/wp-content/uploads/2025/06/logo-pruning-my-pothos.png" alt="Pothos Philosophy Logo" class="story-img" loading="lazy">
      </div>
      <div class="story-text">
        <h2>Pothos: The Plant. The Path.</h2>
        <p>More than just a houseplant, the pothos symbolizes resilience and adaptability. It grows in silence, thrives in neglect, and stretches toward whatever light it can find.</p>
        <p>To prune is to participate. It’s a gentle rebellion against excess, and a mindful return to what matters. Every trim is a choice to grow better, not just bigger.</p>
        <p>We found in pothos a metaphor that mirrors our own loops of healing, restraint, and thoughtful expansion.</p>
        <a href="https://pruningmypothos.com/pruning-pothos-philosophy/" class="read-more-btn">Read the Full Blog</a>
      </div>
    </div>

    <!-- CORE BELIEFS -->
    <div class="about-values-section fade-in">
      <h2>What We Believe</h2>
      <ul class="about-list">
        <li>✂️ Letting go is a creative act</li>
        <li>🌱 Growth isn’t linear — it’s loopy, messy, honest</li>
        <li>🪴 Ideas need space, not pressure</li>
        <li>🍂 Burnout is feedback, not failure</li>
      </ul>
    </div>

    <!-- FINAL CTA -->
    <div class="about-outro fade-in">
      <h2>This Is Not a Cult. (Yet.)</h2>
      <p>If you're into slow growth, soft rebellion, and metaphors with dirt under the nails — you're one of us.</p>
      <a href="/blog" class="cta-btn">→ Start Reading</a>
    </div>

  </div>
</section>

<?php get_footer(); ?>
