# Ren'Py Displaying Images

> **Fetched from:** https://www.renpy.org/doc/html/displaying_images.html  
> **Date:** January 2025  
> **Purpose:** Understanding image management and display for The Plot Thickens project

# Displaying Images

The defining aspect of a visual novel, lending its name to the form, are the visuals. Ren'Py contains four statements that control the display of images, and a model that determines the order in which the images are displayed.

The four statements that work with images are:

- **image** - defines a new image.
- **show** - shows an image on a layer.
- **scene** - clears a layer, and optionally shows an image on that layer.
- **hide** - removes an image from a layer.

As abrupt changes of image can be disconcerting to the user, Ren'Py has the **with** statement, which allows effects to be applied when the scene is changed.

## Concepts

### Image

An image is something that can be shown to the screen using the show statement. An image consists of a **name** and a **displayable**. When the image is shown on a layer, the displayable associated with it is displayed on that layer.

An image name consists of one or more names, separated by spaces. The first component of the image name is called the **image tag**. The second and later components of the name are the **image attributes**.

For example, take the image name `mary beach night happy`. The image tag is `mary`, while the image attributes are `beach`, `night`, and `happy`.

A displayable is something that can be shown on the screen. The most common thing to show is a static image, which can be specified by giving the filename of the image, as a string.

### Layer

A layer is a list of displayables that are shown on the screen. Ren'Py supports multiple layers, including user-defined layers. The following layers are defined as part of Ren'Py:

**master**
: This is the default layer that is used by the scene, show, and hide statements. It's generally used for backgrounds and character sprites.

**transient**
: The default layer used by ui functions. This layer is cleared at the end of each interaction.

**screens**
: This layer is used by the screen system.

**overlay**
: The default layer used when a ui function is called from within an overlay function. This layer is cleared when an interaction is restarted.

## Defining Images

There are two ways to define images. You can either place an image file in the images directory, or an image can be defined using the image statement.

### Images Directory

The image directory is named "images", and is placed under the game directory. When a file with a `.jpg`, `.jpeg`, `.png`, or `.webp` extension is placed underneath this directory, the extension is stripped, the rest of the filename is forced to lowercase, and the resulting filename is used as the image name.

For example, all of these files will define the image `eileen happy`:

```
game/images/eileen happy.png
game/images/Eileen Happy.jpg
game/images/eileen/eileen happy.png
```

### Oversampling

By default, the pixel size of an image defines the size it will take up when displayed. When oversampling is enabled, the size that the image is displayed at is smaller than the image size would imply.

Oversampling is automatically enabled if the image ends with an '@' followed by a number, before the extension. For example:

- `eileen happy@2.png` is 2x oversampled
- `eileen happy@3.png` will be 3x oversampled

### Image Statement

The image statement is used to define an image. An image statement consists of a single logical line beginning with the keyword image, followed by an image name, an equals sign `=`, and a displayable. For example:

```renpy
image eileen happy = "eileen_happy.png"
image black = "#000"
image bg tiled = Tile("tile.jpg")
image eileen happy question = VBox(
    "question.png",
    "eileen_happy.png",
)
```

When an image file is not directly in the game directory, you'll need to give the directories underneath it:

```renpy
image eileen happy = "eileen/happy.png"
```

The image statement is run at init time, before the menus are shown or the start label runs.

## Show Statement

The show statement is used to display an image on a layer. A show statement consists of a single logical line beginning with the keyword show, followed by an image name, followed by zero or more properties.

If the show statement is given the exact name of an existing image, that image is the one that is shown. Otherwise, Ren'Py will attempt to find a unique image that:

- Has the same tag as the one specified in the show statement.
- Has all of the attributes given in the show statement.
- If an image with the same tag is already showing, shares the largest number of attributes with that image.

If an image with the same image tag is already showing on the layer, the new image replaces it. Otherwise, the image is placed above all other images in the layer.

The show statement takes the following properties:

**as**
: The as property takes a name. This name is used in place of the image tag when the image is shown. This allows the same image to be on the screen twice.

**at**
: The at property takes one or more comma-separated simple expressions. Each expression must evaluate to a transform. The transforms are applied to the image in left-to-right order.

**behind**
: Takes a comma-separated list of one or more names. Each name is taken as an image tag. The image is shown behind all images with the given tags that are currently being shown.

**onlayer**
: Takes a name. Shows the image on the named layer.

**zorder**
: Takes an integer. The integer specifies the relative ordering of images within a layer, with larger numbers being closer to the user.

Examples:

```renpy
# Basic show.
show mary night sad

# Since 'mary night sad' is showing, the following statement is
# equivalent to: show mary night happy
show mary happy

# Show an image on the right side of the screen.
show mary night happy at right

# Show the same image twice.
show mary night sad as mary2 at left

# Show an image behind another.
show moon behind mary, mary2

# Show an image on a user-defined layer.
show moon onlayer user_layer
```

### Attributes Management

Attributes can be set, added and replaced. They can also be removed using the minus sign:

```renpy
# show susan being neutral
show susan

# show susan being happy
show susan happy

# show susan being neutral again
show susan -happy
```

### Show Expression

A variant of the show statement replaces the image name with the keyword expression, followed by a simple expression. The expression must evaluate to a displayable:

```renpy
show expression "moon.png" as moon
```

## Scene Statement

The scene statement removes all displayables from a layer, and then shows an image on that layer. It consists of the keyword scene, followed by an image name, followed by zero or more properties.

```renpy
scene bg beach
```

**Scene Expression**: Like the show statement, the scene statement can take expressions instead of image names.

**Clearing a layer**: When the image name is omitted entirely, the scene statement clears all displayables from a layer without showing another displayable.

## Hide Statement

The hide statement removes an image from a layer. It consists of the keyword hide, followed by an image name, followed by an optional property.

```renpy
e "I'm out of here."
hide eileen
```

Hide statements are rarely necessary. If a sprite represents a character, then a hide statement is only necessary when the character leaves the scene. When the character changes her emotion, it is preferable to use the show statement instead.

## With Statement

The with statement is used to apply a transition effect when the scene is changed, making showing and hiding images less abrupt. The with statement consists of the keyword with, followed by a simple expression that evaluates either to a transition object or the special value None.

```renpy
show bg washington with dissolve
show eileen happy at left
show lucy mad at right with dissolve
```

### With None

The with statement changes behavior when given the special value None. The with None statement causes an abbreviated interaction to occur, without changing what the user sees. When the next transition occurs, it will start from the scene as it appears at the end of this abbreviated interaction.

```renpy
show bg washington with None
show eileen happy at left
show lucy mad at right with dissolve
```

### With Clause of Scene, Show, and Hide Statements

The show, scene, and hide statements can take an optional with clause, which allows a transition to be combined with showing or hiding an image:

```renpy
show eileen happy at left with dissolve
show lucy mad at right with dissolve
```

---

**Key Points for The Plot Thickens:**

1. **Image Organization**: Automatic discovery from images/ directory with attribute-based naming
2. **Layer System**: Multiple display layers (master, transient, screens, overlay)
3. **Tag-Attribute Model**: Images organized by tags with modifiable attributes
4. **Transform System**: Positioning and animation through transforms
5. **Oversampling**: High-resolution asset support with automatic scaling
6. **Transition Effects**: Smooth scene changes with transition statements
7. **Asset Management**: Organized file structure and automatic image discovery

This is essential for understanding how Ren'Py projects organize and manage visual assets.
