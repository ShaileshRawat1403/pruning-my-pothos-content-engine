<?php
/*
Template Name: Homepage
*/
get_header();
?>

<div class="homepage-container">

  <!-- HERO SECTION -->
<section class="hero-section">
  <div class="hero-content">
    <h1 id="typewriter" class="typewriter-title"></h1>
    <h3 class="hero-subtitle">Reflecting. Refining. Rejoicing.</h3>

<div class="hero-subtext">
  <p class="hero-line">Tech Transformation. <span>Change Management.</span></p>
  <p class="hero-line">Artificial Intelligence. <span>Natural Ignorance.</span></p>
  <p class="hero-line">Machine Learning. <span>Meaningful Living.</span></p>
</div>

    <div class="hero-cta-buttons">
      <a href="/the-antithesis" id="uncomfortable-btn" class="cta-btn">→ Get Uncomfortable</a>
      <a href="/blog" class="cta-btn secondary">→ Browse Freely</a>
    </div>
  </div>
</section>

<!-- ✅ SAN SERIF SENTIMENTS SECTION -->
<section class="sss-thought-blocks fade-in">
  <div class="sss-heading">
    <h2 class="sss-title">Sans Serif Sentiments</h2>
    <p class="sss-subtitle">(Simple words. Sincere intent.)</p>
    <div class="sss-breakdown">
      <p><strong>Sans</strong> – The absence.</p>
      <p><strong>Serif</strong> – The excess. The embellishment.</p>
      <p><strong>Sentiments</strong> – What’s left when all that’s stripped away.</p>
    </div>
  </div>

  <!-- Thought Block Cards -->
  <div class="thought-blocks-wrapper">
    <div class="thought-block">
      <div class="commit-label">Commit: Define Purpose</div>
      <p>Most people write to inspire.<br>
         A few write to inform.<br>
         Fewer still write to liberate.</p>
    </div>

    <div class="thought-block">
      <div class="commit-label">Commit: Audit Assumptions</div>
      <p>People don’t need more advice.<br>
         They need context.<br>
         They need clarity.<br>
         They need the courage to continue.</p>
    </div>

    <div class="thought-block">
      <div class="commit-label">Commit: Write Responsibly</div>
      <p>Write like it hurts.<br>
         Write like it heals.<br>
         Write like it happened to you.</p>
    </div>

    <div class="thought-block">
      <div class="commit-label">Commit: Preserve Meaning</div>
      <p><em>The what</em> grabs attention.<br>
         <em>The how</em> earns trust.<br>
         <em>The why</em> makes it stay.</p>
    </div>
  </div>

  <!-- CTA Button (now outside the grid) -->
  <div class="cta-block">
<a href="https://pruningmypothos.com/the-antithesis/" class="cta-btn">→ The Antithesis</a>
  </div>
</section>

<!-- BLOG GRID -->
<section class="blog-container">
  <div class="container">
    <h2>Blog Posts</h2>

    <!-- Search Bar for Blog Section -->
    <form role="search" method="get" id="searchform" class="searchform" action="<?php echo home_url('/'); ?>">
      <input type="text" value="<?php echo get_search_query(); ?>" name="s" id="search-bar" placeholder="Search blog posts..." />
      <button type="submit" id="search-btn">
        <i class="fa fa-search"></i> <!-- You can use a magnifying glass icon here -->
      </button>
    </form>
    <!-- End of Search Bar -->

    <?php
    // Ensure that the query only fetches blog posts (post type 'post')
    $offset = 1; // Skip featured post
    $ppp = 15; // Posts per page
    $args = [
      'post_type'      => 'post',         // Ensure it's only 'post' type
      'posts_per_page' => $ppp,           // Limit number of posts
      'offset'         => $offset,        // Skip first post (featured)
      's'              => get_search_query() // Search query parameter (keyword)
    ];

    $main_query = new WP_Query($args);
    $total_posts = wp_count_posts()->publish;
    ?>

    <div id="posts-wrapper" class="blog-grid">
      <?php
      if ($main_query->have_posts()):
        while ($main_query->have_posts()): $main_query->the_post(); ?>
          <article class="post-card">
            <?php if (has_post_thumbnail()): ?>
              <a href="<?php the_permalink(); ?>">
                <?php the_post_thumbnail('medium', ['loading' => 'lazy']); ?>
              </a>
            <?php endif; ?>
            <h2 class="post-title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
            <p><?php echo wp_trim_words(get_the_excerpt(), 20); ?></p>
          </article>
      <?php endwhile; wp_reset_postdata(); else: ?>
        <p>No posts found for "<?php echo get_search_query(); ?>"</p> <!-- Display the searched term -->
      <?php endif; ?>
    </div>

    <?php
    // Load more button functionality
    $loaded_count = $offset + $ppp;
    if ($loaded_count < $total_posts): ?>
      <button id="load-more"
        data-offset="<?php echo $loaded_count; ?>"
        data-ppp="<?php echo $ppp; ?>"
        data-total="<?php echo $total_posts; ?>"
      >Load More</button>
    <?php endif; ?>
  </div>
</section>

  <!-- ABOUT PREVIEW -->
  <section class="about-section">
    <div class="container">
      <h2>About Us</h2>
      <p>Some people collect hobbies, we collect existential crises. <br>
      This is a space for nuance, for questioning, for peeling back the layers of what we think we know. <br>
      If you enjoy wit with a touch of wisdom (or vice versa), you’re in the right place.</p>
      <a href="/about" class="cta-btn">Read the story behind Pruning My Pothos</a>
    </div>
  </section>

  <!-- RESOURCES PREVIEW -->
  <section class="resources-section">
    <div class="container">
      <h2>Resources</h2>
      <p>Hand-picked tools and guides to spark your creativity and sharpen your insights.</p>
      <a href="/resources" class="cta-btn">Explore Resources</a>
    </div>
  </section>

</div>

<?php get_footer(); ?>
