<?php get_header(); ?>

<div class="container">
    <?php if (have_posts()) : while (have_posts()) : the_post(); ?>
        <article class="blog-post">
            <h1 class="post-title"><?php the_title(); ?></h1>
            <p class="post-meta">Published on <?php echo get_the_date(); ?> by <?php the_author(); ?></p>

            <?php if (has_post_thumbnail()): ?>
                <div class="featured-image">
                    <?php the_post_thumbnail('large'); ?>
                </div>
            <?php endif; ?>

            <div class="post-content">
                <?php the_content(); ?>
            </div>

            <div class="post-footer">
                <p><strong>Categories:</strong> <?php the_category(', '); ?></p>
                <p><strong>Tags:</strong> <?php the_tags('', ', ', ''); ?></p>
            </div>

            <div class="post-navigation">
                <?php previous_post_link('%link', '← Previous'); ?>
                <?php next_post_link('%link', 'Next →'); ?>
            </div>

            <div class="comments-section">
                <?php comments_template(); ?>
            </div>
        </article>
    <?php endwhile; endif; ?>
</div>

<?php get_footer(); ?>
